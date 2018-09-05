start-containers: stop-containers
	- docker run --rm -d -p 27017:27017 --name backdrop-mongo mongo:2.4
	- docker run --rm -d -p 5432:5432 --name backdrop-postgres postgres:9.5

.PHONY: stop-containers
stop-containers:
	- docker stop backdrop-mongo
	- docker kill backdrop-mongo
	- docker stop backdrop-postgres
	- docker kill backdrop-postgres

.PHONY: containers-running
containers-running:
	[ -n "$$(docker ps | grep backdrop-mongo)" ] || make start-containers
	[ -n "$$(docker ps | grep backdrop-postgres)" ] || make start-containers

.PHONY: test
test: containers-running
	./run_tests.sh
