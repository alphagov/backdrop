#!/bin/bash -e

VENV_DIR=~/.virtualenvs/$(basename $(cd $(dirname $0) && pwd -P))-$1-$2
LOCK_DIR=./tmp-start

trap "rm -rf $LOCK_DIR" EXIT INT TERM

waiting=0
until mkdir $LOCK_DIR > /dev/null 2>&1; do
    if [ $waiting -eq 0 ]; then
        echo "waiting for startup lock"
        waiting=1
    fi
    sleep 1
done

if [ ! -f "${VENV_DIR}/bin/activate" ]; then
    mkdir -p "${VENV_DIR}"
    virtualenv --no-site-packages "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"

echo "Installing dependencies"
pip install -r requirements.txt

rmdir $LOCK_DIR

python start.py $1 $2
