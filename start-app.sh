#!/bin/bash

basedir=$(dirname $0)

virtualenv --no-site-packages "$basedir/venv"

source "$basedir/venv/bin/activate"

pip install -r requirements.txt

$basedir/venv/bin/python start.py $1 $2