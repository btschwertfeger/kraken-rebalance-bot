# -*- coding: utf-8 -*-

"""Module that serves as entrypoint for the CLI"""
import click


@click.commans()
def run() -> None:
    """Run the Kraken rebalance strategy"""
