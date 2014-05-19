#!/bin/bash -e

declare -a VENV_DIRS=(
    ~/.virtualenvs/$(basename $(cd $(dirname $0) && pwd -P))-read
    ~/.virtualenvs/$(basename $(cd $(dirname $0) && pwd -P))-write
)
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

for VENV_DIR in "${VENV_DIRS[@]}"
do
    if [ ! -f "${VENV_DIR}/bin/activate" ]; then
        mkdir -p "${VENV_DIR}"
        virtualenv --no-site-packages "$VENV_DIR"
    fi
source "$VENV_DIR/bin/activate"

done


echo "Installing dependencies"
pip install -r requirements.txt

rmdir $LOCK_DIR

exec python start.py "read" 3038 &
exec python start.py "write" 3039 &
