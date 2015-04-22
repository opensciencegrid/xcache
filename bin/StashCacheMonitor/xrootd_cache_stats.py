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

    totalsize = 0
    nfiles = 0
    naccesses = 0
    most_recent_access = 0
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
                access_count, access_time = read_cinfo(os.path.join(root, cinfo))
            except OSError, ex:
                if ex.errno == errno.ENOENT:
                    continue
                else: raise

            nfiles += 1
            totalsize += st.st_blocks*512 # allow for sparse files
            naccesses += access_count
            most_recent_access = max(most_recent_access, access_time)

    result = classad.ClassAd({"used_bytes" : totalsize, "nfiles" : nfiles, "naccesses" : naccesses})
    if most_recent_access > 0:
        result["most_recent_access_time"] = most_recent_access
    return result


def read_cinfo(cinfo_file):
    """ Try to extract useful info from the cinfo file """

    cf = open(cinfo_file, 'rb')

    # header (not a c struct; consecutive separate values with no padding)
    # version + buffer size + download status array size (bits) + download status array
    #   int   +  long long  +              int                  +       variable 
    header_fmt = '=iqi'
    header_size = struct.calcsize(header_fmt)
    buf = cf.read(header_size)
    if len(buf) > header_size:
        # a mangled file
        return 0, 0

    version, buffer_size, status_array_size_bits = struct.unpack(header_fmt, buf)

    # only understand version 0
    if version != 0:
        return 0, 0

    # get the size of the status array and skip over it
    status_array_size_bytes = (status_array_size_bits -1)//8 + 1
    cf.seek(status_array_size_bytes, os.SEEK_CUR)

    # now the access count (an int)
    buf = cf.read(4)
    if len(buf) < 4:
        return 0, 0
    access_count, = struct.unpack('@i', buf)

    if access_count <= 0:
        return 0, 0

    # each access contains a struct (native size + padding)
    # detach time + bytes disk + bytes ram + bytes missed
    # time_t      + long long  + long long + long long
    status_fmt = '@lqqq'
    status_size = struct.calcsize(status_fmt)

    # seek to the most recent access
    cf.seek((access_count-1)*status_size, os.SEEK_CUR)
    buf = cf.read(status_size)
    if len(buf) < status_size:
        # this may have caught a partially updated file; should it return the access count and current time?
        return 0, 0
    access_time, _, _, _ = struct.unpack(status_fmt, buf)

    return access_count, access_time


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
    totalsize = 0
    totalnfiles = 0
    totalnaccesses = 0
    most_recent_access = 0
    result['VO'] = {}
    for vo, vostats in stats_per_vo.items():
        totalsize += vostats.get("used_bytes", 0)
        totalnfiles += vostats.get("nfiles", 0)
        totalnaccesses += vostats.get("naccesses", 0)
        most_recent_access = max(most_recent_access, vostats.get("most_recent_access_time", 0))
        result['VO'][vo] = vostats
    result['used_cache_bytes'] = totalsize
    result["total_nfiles"] = totalnfiles
    result["total_naccesses"] = totalnaccesses
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
