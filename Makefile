.DEFAULT_GOAL := help

.PHONY: help
help:
        @echo "Please use 'make <target>' where <target> is one of"
        @echo ""
        @echo "  install     install packages and prepare environment"
        @echo "  clean       remove all temporary files"
        @echo "  lint        run the code linters"
        @echo "  format      reformat code"
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