#! /usr/bin/python
"""
Monitoring functions for xrootd cache server, producing classads
that can be handed to condor
"""

import os
import math
import time
import errno
import struct
import urlparse
import collections

import classad
import XRootD.client

__all__ = ['collect_cache_stats']

# these paths in the cache are to be treated as top level "VOs" for stats collection
vo_paths = [ '/user', '/pnfs/fnal.gov/usr' ]

def _split_path(path):
    """ Split a path into a list of directory names """
    if path[0] != '/':
        raise Exception("Not absolute path")
    result = []
    while path != '/':
        path, tail = os.path.split(path)
        if tail: result.append(tail)
    return list(reversed(result))

def _is_prefix(lhs, rhs):
    """ return True if the first list is a prefix of the second """
    rhs = list(rhs)
    while rhs:
        if lhs == rhs: return True
        rhs.pop()
    return False

def scan_cache_dirs(rootdir):
    """ Scan the top level directory of the cache.
    Walks the path looking for directories that are not in vo_paths.
    For each of these generate a cache summary
    """

    results = {}
    try:
        root_components = _split_path(rootdir)
        for dirpath, dirnames, filenames in os.walk(rootdir, topdown=True):
            # get the path components as a list, removing the rootdir part
            dirpath_components = _split_path(dirpath)[len(root_components):]
            for name in list(dirnames):
                path_components = dirpath_components + [name]
                for p in [ _split_path(p) for p in vo_paths]:
                    # if this directory is in vo_paths, keep recursing
                    if _is_prefix( path_components, p):
                        break
                else:
                    # if nothing is in vo_paths, get the stats and remove from dirnames
                    # so this walk goes no further
                    vo_name = os.path.join('/', *path_components)
                    try:
                        results[vo_name] = scan_vo_dir(os.path.join(dirpath, name))
                    except (OSError, IOError), ex:
                        results[vo_name] = {'scan_vo_dir_error': str(ex) }
                    dirnames.remove(name)
        return results
    except (OSError, IOError), ex:
        return { 'scan_cache_dirs_error' : { 'message' : str(ex) } } # error message?


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
                accesses["bytes_hr_" + h] += access_info["bytes_hr"][h]

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
# version + buffer size + file size (blocks)
# int     + long long   + long long
_header_fmt = '=iqq'
_header_fmt_size = struct.calcsize(_header_fmt)

# then the number of accesses
#   int
_int_fmt = '@q'
_int_fmt_size = struct.calcsize(_int_fmt)

# each access contains a struct (native size + padding)
# AttachTime + DetachTime + BytesDisk + BytesRam  + BytesMissed
# time_t     + long long  + long long + long long + long long
_status_fmt = '@qqqqq'
_status_fmt_size = struct.calcsize(_status_fmt)

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
               "bytes_hr" : { "01": 0, "12": 0, "24": 0 },
             }

    cf = open(cinfo_file, 'rb')

    # read and unpack the header
    buf = cf.read(_header_fmt_size)
    if len(buf) < _header_fmt_size:
        # a mangled file
        raise ReadCInfoError("%s header too short" % cinfo_file, result)

    version, buffer_size, file_size = struct.unpack(_header_fmt, buf)

    # we only understand version 2
    if version != 2:
        raise ReadCInfoError("%s unknown version: %s" % (cinfo_file, version), result)

    # Get the size of the state vector and skip over it
    # buff_synced uses 1 bit per bufferSize block of bytes
    # Length is rounded up to the nearest byte
    buff_synced_len = int(math.ceil(float(file_size)/buffer_size/8))

    # If the file_size is zero, state vector length is 1
    # (Difference is due to Python's integer division returning the floor)
    if file_size == 0:
        buff_synced_len = 1

    cf.read(buff_synced_len)

    # Go past cksum (char[16]) and creationTime (time_t)
    cf.read(16 + 8)

    # now the access count (an int)
    buf = cf.read(_int_fmt_size)
    if len(buf) < _int_fmt_size:
        raise ReadCInfoError("%s: invalid access field" % cinfo_file, result)

    access_count, = struct.unpack(_int_fmt, buf)

    result["naccesses"] = access_count

    if access_count < 0:
        raise ReadCInfoError("%s: invalid access count: %s" % (cinfo_file, access_count), result)
    elif access_count == 0:
        return result

    # read the access times

    hr_01 = now - 60*60
    hr_12 = now - 12*60*60
    hr_24 = now - 24*60*60

    # Read AStat structs
    try:
        for buf in iter(lambda: cf.read(_status_fmt_size), b''):
            access_time, _, bytes_disk, bytes_ram, _ = struct.unpack(_status_fmt, buf)
            result["last_access"] = access_time

            #print access_time, bytes_disk, bytes_ram
            #print time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(access_time))

            intervals = list()
            if access_time >= hr_01: intervals.append('01')
            if access_time >= hr_12: intervals.append('12')
            if access_time >= hr_24: intervals.append('24')
            else:
                # no longer interested
                next

            for interval in intervals:
                result["by_hour"][interval] += 1
                result["bytes_hr"][interval] += bytes_disk + bytes_ram
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

    # Python 2.6's urlparse returns a ParseResult object whereas
    # Python 2.4's urlparse returns a tuple that doesn't handle
    # root:// properly
    try:
        if parsed_url.scheme not in ('root', 'xroot'):
            raise Exception("URL '%s' is not an xrootd url" % url)

        hostname = parsed_url.netloc
    except AttributeError:
        if parsed_url[0] not in ('root', 'xroot'):
            raise Exception("URL '%s' is not an xrootd url" % url)

        hostname = parsed_url[2][2:] # Avoid the '//' prefix

    result = {'MyType' : 'Machine', 'Name': 'xrootd@%s' % hostname, 'stats_time' : int(start_time)}
    result.update(test_xrootd_server(url))
    result.update(get_cache_info(rootdir, cache_max_fs_fraction))

    stats_per_vo = scan_cache_dirs(rootdir)
    # add up the sizes
    totals = dict()
    most_recent_access = 0
    result['VO'] = {}
    for vo, vostats in stats_per_vo.items():
        for k, v in vostats.items():
            if k == "most_recent_access_time":
                most_recent_access = max(most_recent_access, v)
            else:
                try:
                    totals[k] += v
                except KeyError:
                    totals[k] = v
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
