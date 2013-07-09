#!/bin/bash

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

nosetests -v --with-xunit --with-coverage --cover-package=backdrop --cover-inclusive
display_result $? 1 "Unit tests"

behave --stop --tags=-wip
display_result $? 2 "Feature tests"

./pep-it.sh | tee pep8.out
display_result $? 3 "Code style check"
