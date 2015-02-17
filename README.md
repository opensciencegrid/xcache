StashCache
==========

This repo holds json file with addresses, statuses and geographical coordinates of all of the StashCache caches.
Status is given as a number: 1 - Active, 0 - Not Active.

Doing:
source ./setStashCache.(c)sh will determine what is the closest StashCache to the user and export a variable STASHPREFIX containing the address of the closest StashCache.

After that a user can access the file in the following way:

xrdcp $STASHPREFIX/user/ivukotic/xAOD_mc.pool.root xAOD_mc.pool.root