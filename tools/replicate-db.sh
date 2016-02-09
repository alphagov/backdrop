#!/bin/bash -e

set -euo pipefail

#
# Replicate backdrop mongo db from a source host to a target host.
# Useful to import data from the preview environment to the development
# one.
#

if [ "$(hostname)" == "development-1" ]; then
    echo "This script should be run on the host machine, not your virtual machine!"
    exit 1
fi

if [ "$(basename $(pwd))" != 'tools' ]; then
    cd $(dirname $0)
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

# collections to ignore
BLACKLIST='system.indexes\|govuk_asset_requests\|govuk_info_page_statistics'

# ssh to mongo-1 and mongodump
ssh $SOURCE_HOST "mongo backdrop --eval 'rs.slaveOk(); db.getCollectionNames().join(\"\\n\")' --quiet | grep -v '\\(${BLACKLIST}\\)' | xargs -L 1 mongodump -d backdrop -o ${DUMPDIR} -c"

# ssh and tar dump folder
ssh $SOURCE_HOST "tar czvf ${FILENAME} ${DUMPDIR}"

# scp tar
scp $SOURCE_HOST:~/$FILENAME .

# clean up remote machine
ssh $SOURCE_HOST "rm -Rf ${FILENAME} ${DUMPDIR}"

# mongorestore
tar xzvf $FILENAME

if [ -z "$2" ]; then
    pushd ../../pp-puppet/
    vagrant ssh development-1 -c "cd /var/apps/backdrop/tools && mongorestore --drop ${DUMPDIR}"
    popd
elif [ "$2" = 'govuk_dev' ]; then
    pushd ../../govuk-puppet/development
    vagrant ssh -c "cd /var/govuk/backdrop/tools && mongorestore --drop ${DUMPDIR}"
    popd
else
    mongorestore --drop -h $DESTINATION_HOST $DUMPDIR
fi

# cleanup locally
rm -Rf $DUMPDIR
rm -f $FILENAME
