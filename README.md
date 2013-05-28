# Backdrop

##What is it?
Backdrop is a datastore built with python and mongo db. It is made up of two separately deployable APIs for reading and writing data over http. The plan is to be able to gather data from a variety of sources and then aggregate and compare this data in useful ways.

- Data is grouped into buckets.
- Data is stored by posting json to the write api.
- Certain types of data are identified by reserved keys. ie events are objects containing a timestamp.
- Reserved keys start with an underscore. eg `{ "_timestamp": "2013-01-01T00:00:00Z }"`
- Data is retrieved using http query strings on the read api.
- Data can be retrieved in a few useful ways. eg `/<name_of_my_bucket>?period=month` for monthly grouped data.
- Backdrop is in constant development, the best place to find examples and features are the feature tests https://github.com/alphagov/backdrop/tree/master/features

##Getting set up

This assumes you are using the GDS dev environment and so have python and mongo installed.

0. Check that you have virtualenv installed, if not ```sudo apt-get install python-virtualenv```.
1. Navigate to the ```performance-platform``` directory and run ```./run_tests.sh```. This will
create a new virtualenv, install all dependencies and run the tests.
2. ```source venv/bin/activate``` to enable the virtualenv.

