#!/bin/bash

set -o pipefail

VIRTUALENV_DIR=/var/tmp/virtualenvs/$(echo ${JOB_NAME} | tr ' ' '-')
export PIP_DOWNLOAD_CACHE=/var/tmp/pip_download_cache

virtualenv --clear --no-site-packages $VIRTUALENV_DIR
source $VIRTUALENV_DIR/bin/activate

SKIP_SPLINTER_TESTS=1 ./run_tests.sh
