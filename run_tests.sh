#!/bin/bash

function display_result {
    RESULT=$1
    EXIT_STATUS=$2
    TEST=$3

    if [ $RESULT -ne 0 ]; then
      echo
      echo -e "\033[31m$TEST failed\033[0m"
      echo
      exit $EXIT_STATUS
    else
      echo
      echo -e "\033[32m$TEST passed\033[0m"
      echo
    fi
}
basedir=$(dirname $0)
venvdir=~/.virtualenvs/$(basename $(cd $(dirname $0) && pwd -P))

if [ ! -d $venvdir ]; then
  virtualenv $venvdir
fi

source "$venvdir/bin/activate"

pip install -r requirements_for_tests.txt

find . -name '*.pyc' -delete

nosetests -v
display_result $? 1 "Unit tests"

behave --stop --tags=-wip
display_result $? 2 "Feature tests"

"$basedir/pep-it.sh"
display_result $? 3 "Code style check"
