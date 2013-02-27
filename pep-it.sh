#!/bin/bash

basedir=$(dirname $0)
pep8 --ignore=E201,E202,E251 --exclude=venv "$basedir"
