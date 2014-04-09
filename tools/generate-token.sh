#!/bin/bash

#
# Generate a random token 
#

head -c 500 /dev/urandom | shasum -a 512
