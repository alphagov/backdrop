#!/usr/bin/env bash

set -e

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

# bind services
cf bind-service performance-platform-backdrop-read gds-performance-platform-mongodb-service
cf bind-service performance-platform-backdrop-write gds-performance-platform-mongodb-service

# set environmental variables
cf set-env performance-platform-backdrop-read ENVIRONMENT $PAAS_SPACE
cf set-env performance-platform-backdrop-read STAGECRAFT_URL https://performance-platform-stagecraft-$PAAS_SPACE.cloudapps.digital
cf set-env performance-platform-backdrop-read SIGNON_API_USER_TOKEN $APP_SIGNON_API_USER_TOKEN

cf set-env performance-platform-backdrop-write ENVIRONMENT $PAAS_SPACE
cf set-env performance-platform-backdrop-write STAGECRAFT_URL https://performance-platform-stagecraft-$PAAS_SPACE.cloudapps.digital
cf set-env performance-platform-backdrop-write SIGNON_API_USER_TOKEN $APP_SIGNON_API_USER_TOKEN
cf set-env performance-platform-backdrop-write SECRET_KEY $APP_SECRET_KEY
cf set-env performance-platform-backdrop-write REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER

cf set-env performance-platform-backdrop-celery-worker ENVIRONMENT $PAAS_SPACE
cf set-env performance-platform-backdrop-celery-worker STAGECRAFT_OAUTH_TOKEN $APP_STAGECRAFT_OAUTH_TOKEN
cf set-env performance-platform-backdrop-celery-worker REDIS_DATABASE_NUMBER $REDIS_DATABASE_NUMBER

# deploy apps
cf push -f manifest.yml

# create and map routes
cf map-route performance-platform-backdrop-read cloudapps.digital --hostname performance-platform-backdrop-read-$PAAS_SPACE
cf map-route performance-platform-backdrop-write cloudapps.digital --hostname performance-platform-backdrop-write-$PAAS_SPACE
