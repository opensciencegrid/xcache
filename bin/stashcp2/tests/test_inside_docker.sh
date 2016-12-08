#!/bin/sh -xe

OS_VERSION=$1
XRD_CACHE=$2

ls -l /home

# Clean the yum cache
yum -y clean all
yum -y clean expire-cache

# First, install all the needed packages.
rpm -Uvh https://dl.fedoraproject.org/pub/epel/epel-release-latest-${OS_VERSION}.noarch.rpm

yum -y install yum-plugin-priorities
rpm -Uvh https://repo.grid.iu.edu/osg/3.3/osg-3.3-el${OS_VERSION}-release-latest.rpm

yum -y install osg-oasis

echo "user_allow_other" >> /etc/fuse.conf

echo "CVMFS_HTTP_PROXY=DIRECT" >> /etc/cvmfs/default.local
#echo "CVMFS_EXTERNAL_URL=$CVMFS_EXTERNAL_URL" >> /etc/cvmfs/domain.d/osgstorage.org.local

mkdir -p /cvmfs/config-osg.opensciencegrid.org
mkdir -p /cvmfs/oasis.opensciencegrid.org

mount -t cvmfs config-osg.opensciencegrid.org /cvmfs/config-osg.opensciencegrid.org
mount -t cvmfs oasis.opensciencegrid.org /cvmfs/oasis.opensciencegrid.org

# Load modules
set +e
. /cvmfs/oasis.opensciencegrid.org/osg/modules/lmod/current/init/bash 
set -e
module load xrootd

cp /StashCache/bin/caches.json /StashCache/bin/stashcp2/caches.json

# Try copying with no forward slash
/StashCache/bin/stashcp --cache=$XRD_CACHE user/dweitzel/public/blast/queries/query1 ./

result=`md5sum query1 | awk '{print $1;}'`

if [ "$result" != "12bdb9a96cd5e8ca469b727a81593201" ]; then
  exit 1
fi

rm query1

# Perform tests
/StashCache/bin/stashcp --cache=$XRD_CACHE -d /user/dweitzel/public/blast/queries/query1 ./

result=`md5sum query1 | awk '{print $1;}'`

if [ "$result" != "12bdb9a96cd5e8ca469b727a81593201" ]; then
  exit 1
fi

/StashCache/bin/stashcp --cache=$XRD_CACHE -d -r /user/dweitzel/public/blast/queries ./
ls -lah



