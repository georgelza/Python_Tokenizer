
.DEFAULT_GOAL := help
include .env

define HELP

Available commands:

- run: This will call core.
- createtopics: 
- cypher:
- constraints:

- stop: Stop the project.
- start: Start a stopped project.
- down: Tear down the project, clean directories.
- ps: Show all running containers.

- logs: Show/tail logs.
- logsf: Stream logs.

- watch: Watch logs.


endef

export HELP
help:
	@echo "$$HELP"
.PHONY: help


#	docker rmi $(docker images -q --filter "dangling=true")

run:
	docker compose -f docker-compose.yml -p vectorize up -d \
		 mongodb  redis  \
		--remove-orphans 
	

stop:
	docker compose stop

start:
	docker compose start

down:	
	docker compose down 
	cd data/; rm -rf redis
	cd data/; rm -rf mongodb


ps:
	docker compose ps

logs:
	docker compose logs

logsf:
	docker compose logs -f

watch:
	watch docker compose ps
