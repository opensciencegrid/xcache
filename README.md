# OSG XCache packaging

This repository is the OSG implementation of an XCache (XRootD Caching Proxy) setup.
XCache allows one to setup a "cache" server which saves frequently-accessed
files at a specified "origin" to local storage, allowing repeated accesses of the same
resource to be served without having to transfer them multiple times over the wide-area-network.

XCache is not a generic HTTP cache.  Files in the cache do not expire, nor are there
integrity checking mechanism such as HTTP's `ETag`.  Unlike many HTTP caches, it _can_
stream partial responses: if the client requests only a few bytes from a multi-gigabyte
resource, XCache will send the response before the full download completes.

XCache installation is covered in the [OSG documentation](https://opensciencegrid.org/docs/data/stashcache/install-cache/)

## Features

The OSG packaging features:

- Data can be exported via the HTTP, HTTPS, and Xrootd protocols.
- Configurations for both running an origin and running a cache.
- Integrated authentication and authorization for caches.
- Usage monitoring integrated with OSG's monitoring services.

## XCache Consistency Check

This is an **experimental** tool used to look for corrupted **root** files within an XCache server.
Only enable this service if you know what you are doing.

Before enabling the service, plese take a look to the configuration file located at: `/etc/xrootd/xcache-consistency-check.cfg`

To enable this service execute:

```
systemctl start xcache-consistency-check.timer
```
