#!/bin/bash

venvdir=~/.virtualenvs/$(basename $(cd $(dirname $0) && pwd -P))

virtualenv --no-site-packages "$venvdir"

source "$venvdir/bin/activate"

pip install -r requirements.txt

python start.py $1 $2
