#!/bin/bash -e

venvdir=~/.virtualenvs/$(basename $(cd $(dirname $0) && pwd -P))

if [ ! -d "${venvdir}" ]; then
    virtualenv --no-site-packages "$venvdir"
fi

source "$venvdir/bin/activate"

pip install -r requirements.txt

python start.py $1 $2
