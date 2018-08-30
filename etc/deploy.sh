#!/usr/bin/env bash

set -e

function cycle_app() {
    local app_name=$1

    # ensure we don't get caught out by caching problems
    # caused by the same app code having been pushed under a different
    # app name in the same space (for testing purposes, perhaps).
    cf delete -f ${app_name}
    cf push ${app_name} --no-start
}

if [ -z "$1" ]; then
    echo "Missing PAAS space argument"
    echo "  deploy.sh staging|production"
    exit 1
fi

PAAS_SPACE=$1
wget -q -O - https://packages.cloudfoundry.org/debian/cli.cloudfoundry.org.key | sudo apt-key add -
echo "deb http://packages.cloudfoundry.org/debian stable main" | sudo tee /etc/apt/sources.list.d/cloudfoundry-cli.list
sudo apt-get update && sudo apt-get install cf-cli

cf login -u $PAAS_USER -p $PAAS_PASSWORD -a https://api.cloud.service.gov.uk -o gds-performance-platform -s $PAAS_SPACE

# set environmental variables
cycle_app performance-platform-backdrop-read
cf set-env performance-platform-backdrop-read ENVIRONMENT $PAAS_SPACE
cf set-env performance-platform-backdrop-read STAGECRAFT_URL https://performance-platform-stagecraft-$PAAS_SPACE.cloudapps.digital
cf set-env performance-platform-backdrop-read SIGNON_API_USER_TOKEN $APP_SIGNON_API_USER_TOKEN
cf push performance-platform-backdrop-read

cycle_app performance-platform-backdrop-write
cf set-env performance-platform-backdrop-write ENVIRONMENT $PAAS_SPACE
cf set-env performance-platform-backdrop-write STAGECRAFT_URL https://performance-platform-stagecraft-$PAAS_SPACE.cloudapps.digital
cf set-env performance-platform-backdrop-write SIGNON_API_USER_TOKEN $APP_SIGNON_API_USER_TOKEN
cf set-env performance-platform-backdrop-write SECRET_KEY $APP_SECRET_KEY
cf set-env performance-platform-backdrop-write REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER
cf push performance-platform-backdrop-write

cycle_app performance-platform-backdrop-celery-worker
cf set-env performance-platform-backdrop-celery-worker ENVIRONMENT $PAAS_SPACE
cf set-env performance-platform-backdrop-celery-worker STAGECRAFT_OAUTH_TOKEN $APP_STAGECRAFT_OAUTH_TOKEN
cf set-env performance-platform-backdrop-celery-worker REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER
cf push performance-platform-backdrop-celery-worker

cycle_app performance-platform-backdrop-flower
cf set-env performance-platform-backdrop-flower REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER
cf set-env performance-platform-backdrop-flower FLOWER_BASIC_AUTH $FLOWER_BASIC_AUTH
cf push performance-platform-backdrop-flower

# create and map routes
cf map-route performance-platform-backdrop-read cloudapps.digital --hostname performance-platform-backdrop-read-$PAAS_SPACE
cf map-route performance-platform-backdrop-write cloudapps.digital --hostname performance-platform-backdrop-write-$PAAS_SPACE
cf map-route performance-platform-backdrop-flower cloudapps.digital --hostname performance-platform-backdrop-flower-$PAAS_SPACE
