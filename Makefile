.DEFAULT_GOAL := help

.PHONY: help
help:
		@echo "Please use 'make <target>' where <target> is one of"
		@echo ""
		@echo "  setup     install packages and prepare environment"
		@echo "  run      start pruner"
		@echo "  test        run all the tests"
		@echo ""
		@echo "Check the Makefile to know exactly what each target is doing."

setup: pyproject.toml poetry.lock
	poetry install

.PHONY: test
test:
	python3 -m unittest tests/test_push_gateway_pruner.py

run:
	python3 push_gateway_pruner.py