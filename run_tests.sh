#!/bin/bash -e

set -o pipefail

function display_result {
  RESULT=$1
  EXIT_STATUS=$2
  TEST=$3

  if [ $RESULT -ne 0 ]; then
    echo -e "\033[31m$TEST failed\033[0m"
    exit $EXIT_STATUS
  else
    echo -e "\033[32m$TEST passed\033[0m"
  fi
}

# If you're not already in a virtualenv and you're using virtualenvwrapper
if [ -z "$VIRTUAL_ENV" -a -n "$WORKON_HOME" ]; then
  basedir=$(dirname $0)
  venvdir=$WORKON_HOME/$(basename $(cd $(dirname $0) && pwd -P))

  if [ ! -d "$venvdir" ]; then
    virtualenv $venvdir
  fi

  source "$venvdir/bin/activate"
fi


pip install -r requirements_for_tests.txt

rm -f coverage.xml .coverage nosetests.xml
find . -name '*.pyc' -delete

if [ -z "$NO_AUTOPEP8" ]; then
  autopep8 -i -r backdrop
fi

# run doctests -- breaks if run with main tests
nosetests -v --with-xunit --with-coverage --cover-package=backdrop --with-doctest backdrop

# run unit tests
nosetests -v --with-xunit --with-coverage --cover-package=backdrop
display_result $? 1 "Unit tests"

# create coverage report
python -m coverage.__main__ xml --include=backdrop*

# run feature tests

# NOTE: Skipping tests using tags does not prevent their context from being
#       created, meaning we still instantiate ie a SplinterClient for skipped
#       tests(!) Our python code *also* has to change to get round this... yuk.

if [ "${SKIP_SPLINTER_TESTS}" != "" ] ; then
    behave --stop --tags=~@wip --tags=~@use_admin_client
else
    behave --stop --tags=~@wip
fi

display_result $? 2 "Feature tests"

# run style checks
./pep-it.sh | tee pep8.out
display_result $? 3 "Code style check"

