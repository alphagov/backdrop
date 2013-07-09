#!/bin/bash

#
# Generate a random token 
#

head -c 500 /dev/random | shasum -a 512
