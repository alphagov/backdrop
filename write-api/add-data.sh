#!/bin/bash

if [ $# -eq 0 ]
  then
    echo Usage ./add-data.sh bucket_name json_to_post
fi

curl -H "Content-type: application/json" -X POST "http://www.dev.gov.uk:5000/$1/" -d "$2"
