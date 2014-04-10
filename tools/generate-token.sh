#!/bin/bash

#
# Generate a random token
#

# LC_CTYPE=C is specified for OS X, as otherwise tr will return
# an illegal byte sequence from assuming /dev/urandom is UTF-8

cat /dev/urandom | LC_CTYPE=C tr -cd 'a-z0-9' | tr -d '01oil' | head -c 64

echo '' # Add a newline
