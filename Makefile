.PHONY: test lint format run

test:
	pytest -q

lint:
	ruff check .

format:
	ruff format .

run:
	solo-company run "Build a runnable demo web/API project for learners."
