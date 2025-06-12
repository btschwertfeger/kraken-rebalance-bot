# -*- coding: utf-8 -*-
#
# Copyright (C) 2023 Benjamin Thomas Schwertfeger
# https://github.com/btschwertfeger
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see
# https://www.gnu.org/licenses/gpl-3.0.html.
#

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
