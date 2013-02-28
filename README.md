A minimal repo for spiking out getting hold of some licencing performance data.

1. `sudo pip install -r requirements.txt`
1. Get client secrets from your [Google API Console](https://code.google.com/apis/console/) by creating a new project, turning on Analytics API, going to "API access" and creating an OAuth client ID (name is irrelevant, application type is "Installed application") and click "Download JSON".
1. Put the obtained `client_secrets.json` into the `collectors` folder.
1. Check you can fetch the sample data with `python licensing_location_data.py`. This should output JSON.
1. Put the sample data into mongo with `sh shove-data-into-mongo.sh`.

Would you like a crontab to collect data each month?
`./set-crontab.sh`

# The APIs

##Getting set up

This assumes you are using the GDS dev environment and so have python and mongo installed.

0. Check that you have virtualenv installed, if not ```sudo apt-get install python-virtualenv```.
1. Navigate to the ```performance-platform``` directory and run ```./run_tests.sh```. This will
create a new virtualenv, install all dependencies and run the tests.
2. ```source venv/bin/activate``` to enable the virtualenv.

