#!/bin/bash

set -e

source ./venv/bin/activate

behave
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo 'user tests failed'
  exit 1
fi

nosetests -v
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo 'developer tests failed'
  exit 2
fi

exit 0
