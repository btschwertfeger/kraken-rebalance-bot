#!make
# -*- coding: utf-8 -*-
# Copyright (C) 2023 Benjamin Thomas Schwertfeger
# GitHub: https://github.com/btschwertfeger

PYTHON := python

.PHONY := build dev install clean pre-commit

help:
	@grep "^##" Makefile | sed -e "s/##//"

## ======= B U I L D I N G =======
## build		Builds the python-kraken-sdk
##
build:
	$(PYTHON) -m build .

rebuild: clean build

## dev		Installs the extended package in edit mode
##
dev:
	$(PYTHON) -m pip install -e ".[dev]"

## ======= I N S T A L L A T I O N =======
## install	Install the package
##
install:
	$(PYTHON) -m pip install .

## ======= M I S C E L A N I O U S =======
## pre-commit	Run the pre-commit targets
##
pre-commit:
	@pre-commit run -a


## clean		Clean the workspace
##
clean:
	rm -rf .pytest_cache build/ dist/ \
		kraken_rebalance_bot.egg-info \
		docs/_build \
		.vscode \
		.mypy_cache

	rm -f .coverage coverage.xml pytest.xml mypy.xml \
		rebalance/_version.py \
		*.log *.csv *.zip \
		tests/*.zip tests/.csv \
		kraken_rebalance_bot*.whl

	find tests -name "__pycache__" | xargs rm -rf
	find rebalance -name "__pycache__" | xargs rm -rf
	find examples -name "__pycache__" | xargs rm -rf
