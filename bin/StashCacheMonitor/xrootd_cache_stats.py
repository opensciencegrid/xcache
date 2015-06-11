#! /usr/bin/python
"""
Monitoring functions for xrootd cache server, producing classads
that can be handed to condor
"""

import os
import time
import errno
import struct
import urlparse
import collections

import classad
import XRootD.client

__all__ = ['collect_cache_stats']

def scan_cache_dirs(rootdir):
    """ Scan the top level directory of the cache.
    Assume that each subdir is a separate VO which should be summarized """

    results = {}
    try:
        subdirs = os.listdir(rootdir)
        for name in subdirs:
            if os.path.isdir(os.path.join(rootdir, name)):
                results[name] = scan_vo_dir(os.path.join(rootdir, name))
        return results
    except (OSError, IOError), ex:
        return {} # error message?


def scan_vo_dir(vodir):
    """ Scan a VO directory (assumed to be the whole directory tree after the top level """

    now = time.time()
    totalsize = 0
    nfiles = 0
    naccesses = 0
    accesses = collections.defaultdict(int)
    most_recent_access = 0
    bad_cinfo_files = 0
    for root, dirs, files in os.walk(vodir):
        fnames = set(files)
        # Somebody might add a file ending in .cinfo in the cache
        # so look for the f, f.cinfo pair
        for f, cinfo in ((f, f + '.cinfo') for f in fnames if f + '.cinfo' in fnames):
            try:
                st = os.stat(os.path.join(root, f))
            except OSError, ex:
                if ex.errno == errno.ENOENT:
                    # must have just been deleted
                    continue
                else: raise
            try:
                access_info = read_cinfo(os.path.join(root, cinfo), now)
            except OSError, ex:
                if ex.errno == errno.ENOENT:
                    continue
                else:
                    bad_cinfo_files += 1
                    access_info = { "naccesses" : 0, "last_access": 0, "by_hour" : {} }
            except ReadCInfoError, ex:
                bad_cinfo_files += 1
                access_info = ex.access_info

            nfiles += 1
            file_size = st.st_blocks*512 # allow for sparse files
            totalsize += file_size
            naccesses += access_info["naccesses"]
            most_recent_access = max(most_recent_access, access_info["last_access"])

            for h in access_info["by_hour"]:
                accesses["naccesses_hr_" + h] += access_info["by_hour"][h]
                accesses["bytes_hr_" + h] += access_info["by_hour"][h]*file_size

    result = classad.ClassAd({
                            "used_bytes" : totalsize,
                            "nfiles" : nfiles,
                            "naccesses" : naccesses,
                            "bad_cinfo_files" : bad_cinfo_files
                            })
    result.update(accesses)
    if most_recent_access > 0:
        result["most_recent_access_time"] = most_recent_access
    return result


# Parsing the cinfo files

# The header (not a c struct; consecutive separate values with no padding)
# version + buffer size + download status array size (bits) + download status array
#   int   +  long long  +              int                  +       variable
_header_fmt = struct.Struct('=iqi')

# then the number of accesses
#   int
_int_fmt = struct.Struct('@i')

# each access contains a struct (native size + padding)
# detach time + bytes disk + bytes ram + bytes missed
# time_t      + long long  + long long + long long
_status_fmt = struct.Struct('@lqqq')

class ReadCInfoError(Exception):
    def __init__(self, *args):
        Exception.__init__(self, *args)
        if len(args) > 1:
            self.access_info = args[1]
        else:
            self.access_info = {}

def read_cinfo(cinfo_file, now):
    """ Try to extract useful info from the cinfo file """

    result = { "naccesses": 0,
               "last_access": 0,
               "by_hour" : { "01": 0, "12": 0, "24": 0 },
             }

    cf = open(cinfo_file, 'rb')

    # read and unpack the header
    buf = cf.read(_header_fmt.size)
    if len(buf) < _header_fmt.size:
        # a mangled file
        raise ReadCInfoError("%s header too short" % cinfo_file, result)

    version, buffer_size, status_array_size_bits = _header_fmt.unpack(buf)

    # we only understand version 0
    if version != 0:
        raise ReadCInfoError("%s unknown version: %s" % (cinfo_file, version), result)

    # get the size of the status array and skip over it
    status_array_size_bytes = (status_array_size_bits - 1)//8 + 1
    cf.seek(status_array_size_bytes, os.SEEK_CUR)

    # now the access count (an int)
    buf = cf.read(_int_fmt.size)
    if len(buf) < _int_fmt.size:
        raise ReadCInfoError("%s: invalid access field" % cinfo_file, result)

    access_count, = _int_fmt.unpack(buf)

    result["naccesses"] = access_count

    if access_count < 0:
        raise ReadCInfoError("%s: invalid access count: %s" % (cinfo_file, access_count), result)
    elif access_count == 0:
        return result

    # read the access times

    hr_01 = now - 60*60
    hr_12 = now - 12*60*60
    hr_24 = now - 24*60*60

    # seek to the most recent access and work backwards
    start_pos = cf.tell() # don't go before this

    try:
        cf.seek(-_status_fmt.size, os.SEEK_END)
        buf = cf.read(_status_fmt.size)
        access_time, _, _, _ = _status_fmt.unpack(buf)
        result["last_access"] = access_time
        while True:
            if access_time >= hr_01: result["by_hour"]["01"] += 1
            if access_time >= hr_12: result["by_hour"]["12"] += 1
            if access_time >= hr_24: result["by_hour"]["24"] += 1
            else:
                # no longer interested
                break

            cf.seek(-2*_status_fmt.size, os.SEEK_CUR)
            if cf.tell() < start_pos:
                # done them all
                break
            buf = cf.read(_status_fmt.size)
            access_time, _, _, _ = _status_fmt.unpack(buf)
    except struct.error, ex:
        # return what we've got
        raise ReadCInfoError("%s unable to decode access time data: %s" % (cinfo_file, str(ex)), result)

    return result


def test_xrootd_server(url):
    """ Contact the xrootd server to check if it's alive
    """
    try:
        myclient = XRootD.client.FileSystem(url)
        startt = time.time()
        response, _ = myclient.ping(timeout=10)
        elapsed = time.time() - startt

        if response.fatal:
            status = "fatal"
        elif response.error:
            status = "error"
        elif response.ok:
            status = "ok"
        else:
            status = "unknown"

        result = {"ping_response_status" : status, "ping_response_code" : response.code,
                "ping_response_message" : response.message, "ping_elapsed_time" : elapsed}

        return result

    except Exception, ex: # more specific exception would be better
        return {"ping_response_status" : "failed", "ping_response_code" : -1,
                "ping_response_message" : str(ex), "ping_elapsed_time" : 0.0}


def get_cache_info(rootdir, cache_max_fs_fraction):
    """Get information about the cache itself"""
    result = {}
    try:
        stat = os.statvfs(rootdir)

        total_size = int(stat.f_blocks*stat.f_bsize*cache_max_fs_fraction)
        free_size = int(total_size - (stat.f_blocks-stat.f_bfree)*stat.f_bsize)

        result['total_cache_bytes'] = total_size
        result['free_cache_bytes'] = free_size
        result['free_cache_fraction'] = 1 - float(stat.f_blocks-stat.f_bfree)/int(stat.f_blocks*cache_max_fs_fraction)

        return result
    except (OSError, IOError), ex:
        return {}


def collect_cache_stats(url, rootdir, cache_max_fs_fraction=1.0):
    """ Collect stats on the cache server """
    start_time = time.time()

    parsed_url = urlparse.urlparse(url)

    if parsed_url.scheme not in ('root', 'xroot'):
        raise Exception("URL '%s' is not an xrootd url" % url)

    hostname = parsed_url.netloc

    result = {'MyType' : 'Machine', 'Name': 'xrootd@%s' % hostname, 'stats_time' : int(start_time)}
    result.update(test_xrootd_server(url))
    result.update(get_cache_info(rootdir, cache_max_fs_fraction))

    stats_per_vo = scan_cache_dirs(rootdir)
    # add up the sizes
    totals = collections.defaultdict(int)
    most_recent_access = 0
    result['VO'] = {}
    for vo, vostats in stats_per_vo.items():
        for k, v in vostats.items():
            if k == "most_recent_access_time":
                most_recent_access = max(most_recent_access, v)
            else:
                totals[k] += v
        result['VO'][vo] = vostats
    result['used_cache_bytes'] = totals.pop("used_bytes", 0)
    for k, v in totals.items():
        result["total_" + k] = v
    if most_recent_access > 0:
        result["most_recent_access_time"] = most_recent_access

    result['time_to_collect_stats'] = time.time() - start_time
    return classad.ClassAd(result)


if __name__ == '__main__':
    import sys
    args = sys.argv[1:]
    if len(args) > 2:
        args[2] = float(args[2])
    elif len(args) == 2:
        args.append(0.99) # max cache fraction
    print collect_cache_stats(*args)
