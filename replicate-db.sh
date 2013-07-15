#!/bin/bash

#
# Replicate backdrop mongo db from a source host to a target host.
# Useful to import data from the preview environment to the development
# one.
#

if [ "$(hostname)" == "vm" ]; then
       echo "This script should be run on the host machine!"
       exit 1
fi

if [ $# -lt 1 ]; then
	echo "The script requires at least one argument."
	echo
	echo "Replicate backdrop data from a source host to a target host."
	echo
	echo "Usage:"
	echo "  $(basename $0) <user@source_host> [<target_host>]"
	echo 
	echo "Example:"
	echo "  $(basename $0) youruser@mongo dev.machine"
	echo "    This will run mongorestore on the host machine against the specified target host"
	echo "  $(basename $0) youruser@mongo"
	echo "    This will run mongorestore from within the development VM"
	echo

	exit 2
fi

SOURCE_HOST=$1
DESTINATION_HOST=$2

DATE=$(date +'%Y%m%d-%H%M%S')
DUMPDIR="dump-$DATE"
FILENAME="backdrop-$DATE.tar.gz"

# ssh to mongo-1 and mongodump
ssh $SOURCE_HOST "mongodump -d backdrop -o ${DUMPDIR}"

# ssh and tar dump folder
ssh $SOURCE_HOST "tar czvf ${FILENAME} ${DUMPDIR}"

# scp tar
scp $SOURCE_HOST:~/$FILENAME .

# cleanup preview machine
ssh $SOURCE_HOST "rm -Rf ${FILENAME} ${DUMPDIR}"

# mongorestore
tar xzvf $FILENAME

if [ -z "$2" ]; then
	VAGRANT_CWD=../development vagrant ssh -c "cd /var/govuk/backdrop && mongorestore ${DUMPDIR}"
else
	mongorestore -h $DESTINATION_HOST $DUMPDIR
fi

# cleanup locally
rm -Rf $DUMPDIR
