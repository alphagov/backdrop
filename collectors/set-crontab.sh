#!/bin/sh

APP_DIR=$(cd $(dirname $0); pwd -P)

cron_line='0 5 1 * * /usr/bin/env python '$APP_DIR'/licensing_location_data.py > '$APP_DIR'/ASSETS/location.json # this-is-our-tag'

echo "$(crontab -l | grep -v '# this-is-our-tag')\n$cron_line" | crontab

