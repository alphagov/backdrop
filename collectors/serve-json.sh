#!/bin/sh

APP_DIR=$(cd $(dirname $0); pwd -P)

cd "$APP_DIR/ASSETS"
python -m SimpleHTTPServer
