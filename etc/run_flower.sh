#!/usr/bin/env bash

set -ueo pipefail

: "${VCAP_SERVICES:?Expecting VCAP_SERVICES to be set!}"
: "${REDIS_DATABASE_NUMBER:?Expecting REDIS_DATABASE_NUMBER to be set!}"
: "${PORT:?Expecting PORT to be set!}"
: "${FLOWER_BASIC_AUTH:?Expecting FLOWER_BASIC_AUTH to be set!}"

export FLOWER_BROKER_API="$(echo ${VCAP_SERVICES} | jq -r '.["redis"][] | select(.name == "redis") | .credentials.uri')/${REDIS_DATABASE_NUMBER}"
export FLOWER_PORT=${PORT}

flower --broker="${FLOWER_BROKER_API}" -A backdrop.transformers.worker
