#!/bin/bash

set -e

if [ -e venv ]; then
  rm -r venv
fi
virtualenv venv
source ./venv/bin/activate

pip install -r requirements.txt
pip install -r requirements_for_tests.txt

behave
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo 'user tests failed'
  exit 1
fi

nosetests
RESULT=$?

if [ $RESULT -ne 0 ]; then
  echo 'developer tests failed'
  exit 2
fi

exit 0
