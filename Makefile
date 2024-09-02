.PHONY:
.SILENT:

run:
	python -m src.main

docker-run:
	docker-compose build
	docker-compose up
