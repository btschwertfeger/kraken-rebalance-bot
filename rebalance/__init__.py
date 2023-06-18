#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Copyright (C) 2023 Benjamin Thomas Schwertfeger
# GitHub: https://github.com/btschwertfeger

"""Module that serves as entrypoint for the CLI"""

import json
import logging
import sys
import traceback

import click

from rebalance.bot import RebalanceBot

logging.basicConfig(
    format="%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s",
    datefmt="%Y/%m/%d %H:%M:%S",
    level=logging.INFO,
)


def parse_config(_ctx: click.Context, _param: dict, value: str) -> dict:
    """Callback used to load the config"""

    try:
        with open(value, "r", encoding="utf-8") as json_file:
            return json.load(json_file)  # type: ignore[no-any-return]

    except FileNotFoundError:
        logging.error(f"Config file {value} not found!")
        sys.exit(1)


@click.command()
@click.option("--api-key", type=str, required=True, help="The Kraken API key")
@click.option("--secret-key", type=str, required=True, help="The Kraken secret key")
@click.option(
    "--config",
    required=True,
    type=str,
    help="Path to config file",
    callback=parse_config,
)
def run(api_key: str, secret_key: str, config: dict) -> None:
    """Run the Kraken rebalance strategy"""

    bot: RebalanceBot = RebalanceBot(key=api_key, secret=secret_key, config=config)

    try:
        bot.run()
    except Exception as exc:
        logging.error(f"Bot encountered some exception: {exc} {traceback.format_exc()}")
