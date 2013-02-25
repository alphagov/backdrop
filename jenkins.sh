#!/bin/bash

set -e

if [ -e venv ]; then
  rm -r venv
fi
virtualenv venv
source ./venv/bin/activate

pip install -r requirements.txt
pip install -r requirements_for_tests.txt

./run_tests.sh
