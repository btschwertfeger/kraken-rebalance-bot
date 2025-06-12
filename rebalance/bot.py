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
# pylint: disable=too-many-branches,too-many-statements

"""Module that implements the rebalance strategy"""

import logging
import sys
import time

import requests
import schedule
from kraken.spot import Market, Trade, User


class RebalanceBot:
    """
    Class that implements the Rebalance Strategy

    ===== PARAMETERS =====

    key: str
        Kraken API Public Key
    secret: str
        Kraken API Secret Key
    config: dict
        Configurations

    ===== EXAMPLE =====

    bot = RebalanceBot(
        key='public-key',
        secret='secret-key',
        config={
            'base_currency': ['ETH'],
            'quote_currency': ['USD'],
            'target_quantity': [1000],
            'quote_to_maintain': [500],
            'margin': [0.05],
            'demo': false,
            "telegram": { # optional
                "token": "your telegram token",
                "chat_id": "your telegram chat id"
            },
            'use_build_in_scheduler': false, # optional
        }
    )
    bot.run()
    """

    TIMES: list[str] = ["00:00", "06:00", "12:00", "18:00"]

    def __init__(self, key: str, secret: str, config: dict):
        self.__market: Market = Market()
        self.__trade: Trade = Trade(key=key, secret=secret)
        self.__user: User = User(key=key, secret=secret)

        self.__use_telegram: bool = False
        self.__demo: bool = True
        self.__config: dict = config
        self.__check_config()

    def run(self: "RebalanceBot") -> None:
        """Runs the bot"""
        logging.info("Starting the kraken-rebalance-bot")

        if self.__config.get("use_build_in_scheduler", False):
            logging.info(f'Using scheduled times @{self.__config["times"]}')
            for schedule_time in self.__config["times"]:
                schedule.every().day.at(schedule_time).do(self.__check_balances)

            while True:
                schedule.run_pending()
                time.sleep(60)

        else:
            self.__check_balances()
            sys.exit(0)

    def __check_balances(self: "RebalanceBot") -> None:
        """Checks if buy or sell order must be placed"""
        logging.info("Checking balances ...")

        for i, base_currency in enumerate(self.__config["base_currency"]):
            quote_to_maintain = self.__config["quote_to_maintain"][i]
            target_quantity = self.__config["target_quantity"][i]
            quote_currency = self.__config["quote_currency"][i]
            margin = self.__config["margin"][i]

            available_balance_base: float = float(
                self.__user.get_balance(currency=base_currency)["available_balance"]
            )
            available_balance_quote: float = float(
                self.__user.get_balance(currency=quote_currency)["available_balance"]
            )

            ticker: dict = self.__market.get_ticker(
                pair=f"{base_currency}{quote_currency}"
            )
            symbol: str = list(ticker.keys())[0]
            price: float = float(ticker[symbol]["c"][0])
            value_of_base: float = available_balance_base * price

            msg: str = f"\n👑 {symbol} Rebalance Bot"
            msg += f"\n├ Price: {price} "
            msg += f"\n├ Available {base_currency} » {available_balance_base} ({value_of_base} {quote_currency} / {target_quantity} {quote_currency})"
            msg += f"\n└ Available {quote_currency} » {available_balance_quote}"
            logging.info(f"\n{msg}")

            rebalanced: bool = False
            # check range is left
            if value_of_base <= target_quantity - target_quantity * margin:
                # check if buy would not break quantity to maintain
                if (
                    available_balance_quote
                    > quote_to_maintain + target_quantity - value_of_base
                ):
                    # check if price is higher than the defined max buy price to avoid catching the falling knife
                    if price >= self.__config["lowest_buy_price"][i]:
                        self.__rebalance(
                            symbol=symbol,
                            side="buy",
                            index=i,
                            available={
                                "base": available_balance_base,
                                "quote": available_balance_quote,
                            },
                            last_price=float(ticker[symbol]["c"][0]),
                        )
                        rebalanced = True
                    else:
                        msg = f'{symbol}: not buying because price ({price} {quote_currency}) is lower than the specified lowest buy price ({self.__config["lowest_buy_price"][i]} {quote_currency}).'
                        logging.info(msg)

                else:
                    msg = f"{symbol}: Not enough {quote_currency} to buy more {base_currency}. Noting changed."
                    logging.info(msg)

            # check if new sell
            elif value_of_base >= target_quantity + target_quantity * margin:
                self.__rebalance(
                    symbol=symbol,
                    side="sell",
                    index=i,
                    available={
                        "base": available_balance_base,
                        "quote": available_balance_quote,
                    },
                    last_price=float(ticker[symbol]["c"[0]]),
                )
                rebalanced = True
            if rebalanced:
                # wait to ensure that Krakens backend swallowed all requests
                # to ensure the fetched balances match the actual balances
                time.sleep(3)
                available_balance_base = self.__user.get_balance(
                    currency=base_currency
                )["available_balance"]

                value_of_base = available_balance_base * float(
                    self.__market.get_ticker(pair=symbol)[symbol]["c"][0]
                )

                msg = f"👑 {symbol} Rebalance Bot updated values"
                msg += f"\n├ Available {base_currency} » {available_balance_base} ({value_of_base} {quote_currency} / {target_quantity} {quote_currency})"
                msg += f'\n└ Available {quote_currency} » {self.__user.get_balance(currency=quote_currency)["available_balance"]}'
                logging.info(f"\n{msg}")
            else:
                msg += "\n... nothing changed."

            self.send_to_telegram(message=msg)
            time.sleep(1)

    def __rebalance(  # pylint: disable=too-many-positional-arguments
        self: "RebalanceBot",
        symbol: str,
        side: str,
        index: int,
        available: dict,
        last_price: float,
    ) -> None:
        """Places buy and sell orders"""
        msg: str = f"Rebalancing {symbol} ..."
        logging.info(msg)

        quote_volume: float = float(self.__config["target_quantity"][index]) - (
            available["base"] * last_price
        )

        base_volume: str = self.__trade.truncate(
            amount=abs(quote_volume) / float(last_price),
            amount_type="volume",
            pair=symbol,
        )

        msg = f'✅ {side[0].upper()}{side[1:]} {base_volume} {self.__config["base_currency"][index]} around {last_price} '
        msg += f'{self.__config["quote_currency"][index]} (volume: {quote_volume} {self.__config["quote_currency"][index]})'
        logging.info(msg)
        self.send_to_telegram(message=msg)

        if self.__demo:
            return

        if side == "buy":
            response = self.__trade.create_order(
                ordertype="market", side="buy", pair=symbol, volume=base_volume
            )
            logging.debug(f"Placed order response: {response}")

        if side == "sell":
            response = self.__trade.create_order(
                ordertype="market", side="sell", pair=symbol, volume=base_volume
            )
            logging.debug(f"Placed order response: {response}")

    def __check_config(self: "RebalanceBot") -> None:
        """Checks the config for missing or wrong values"""

        if "base_currency" in self.__config:
            if not isinstance(self.__config["base_currency"], list):
                raise TypeError("base_currency must be type List[str] in config.")
            if len(self.__config["base_currency"]) == 0:
                raise TypeError("No pair(s) specified in config.")
            if (
                len(
                    [
                        pair
                        for pair in self.__config["base_currency"]
                        if not isinstance(pair, str)
                    ]
                )
                != 0
            ):
                raise TypeError("Each pair in config must be type str.")
        else:
            raise TypeError("Missing base_currency in config file.")

        if "quote_currency" in self.__config:
            if not isinstance(self.__config["quote_currency"], list):
                raise TypeError("quote_currency must be type List[str] in config.")
            if len(self.__config["quote_currency"]) == 0:
                raise ValueError("No pair(s) specified in config.")
            if (
                len(
                    [
                        pair
                        for pair in self.__config["quote_currency"]
                        if not isinstance(pair, str)
                    ]
                )
                != 0
            ):
                raise TypeError("Each pair in config must be type str.")
        else:
            raise TypeError("Missing quote_currency in config file.")

        # ___quantity____
        if "target_quantity" in self.__config:
            if not isinstance(self.__config["target_quantity"], list):
                raise TypeError("No quantity in config must be type list[float].")
            if len(self.__config["target_quantity"]) == 0:
                raise TypeError("No quantity defined in config.")
            if (
                len(
                    [
                        q
                        for q in self.__config["target_quantity"]
                        if not isinstance(q, int) and not isinstance(q, float)
                    ]
                )
                != 0
            ):
                raise TypeError("target_quantity must be type int or float in config.")
        else:
            raise TypeError("No target_quantity defined in config.")

        # ___QUOTE_TO_MAINTAIN____
        if "quote_to_maintain" in self.__config:
            if not isinstance(self.__config["quote_to_maintain"], list):
                raise TypeError(
                    "No quote_to_maintain in config must be type List[float]."
                )
            if len(self.__config["quote_to_maintain"]) == 0:
                raise TypeError("No quote_to_maintain specified.")
            if (
                len(
                    [
                        q
                        for q in self.__config["quote_to_maintain"]
                        if not isinstance(q, float) and not isinstance(q, int)
                    ]
                )
                != 0
            ):
                raise TypeError(
                    "quote_to_maintain must be type int or float in config."
                )
        else:
            raise ValueError("No quote_to_maintain defined in config.")

        # ___MARGIN___
        if "margin" in self.__config:
            if not isinstance(self.__config["margin"], list):
                raise TypeError("margin should be type list[str].")
            if (
                len(
                    [
                        m
                        for m in self.__config["margin"]
                        if not isinstance(m, float) or m >= 0.99
                    ]
                )
                != 0
            ):
                raise TypeError(
                    "Margin should be less than 0.99, e.g. 0.04 for a 4% rebalance."
                )
        else:
            raise TypeError("No margin defined in config.")

        if "lowest_buy_price" in self.__config:
            if not isinstance(self.__config["lowest_buy_price"], list):
                raise TypeError("lowest_buy_price should be type List[float].")
        else:
            self.__config["lowest_buy_price"] = [0.0] * len(
                self.__config["target_quantity"]
            )

        # ___MATCHING_PARAMETERS____
        if (
            len(self.__config["base_currency"]) != len(self.__config["target_quantity"])
            or len(self.__config["base_currency"])
            != len(self.__config["quote_currency"])
            or len(self.__config["base_currency"]) != len(self.__config["margin"])
            or len(self.__config["base_currency"])
            != len(self.__config["quote_to_maintain"])
            or len(self.__config["base_currency"])
            != len(self.__config["lowest_buy_price"])
        ):
            raise ValueError(
                "Lengths of: base_currency, quantity, margin, quote_to_maintain, and lowest_buy_price must be the same."
            )

        if "times" in self.__config:
            if (
                not isinstance(self.__config["times"], list)
                or len([t for t in self.__config["times"] if not isinstance(t, str)])
                != 0
            ):
                raise TypeError("times must be type List[str] in config.")
        else:
            logging.warning(
                'No times specfied in config. Default ["00:00", "06:00", "12:00", "18:00"] will be used.'
            )
            self.__config["times"] = self.TIMES

        if "telegram" in self.__config:
            if (
                "token" in self.__config["telegram"]
                and self.__config["telegram"]["token"]
                and "chat_id" in self.__config["telegram"]
                and self.__config["telegram"]["chat_id"]
            ):
                self.__use_telegram = True

        if "demo" in self.__config and isinstance(self.__config["demo"], bool):
            self.__demo = self.__config["demo"]
            logging.info("Demo mode active, not trading.")

    def send_to_telegram(self: "RebalanceBot", message: str) -> None:
        """Send a Message to telegram"""
        if not self.__use_telegram:
            return

        requests.post(
            f'https://api.telegram.org/bot{self.__config["telegram"]["token"]}/sendMessage?chat_id={self.__config["telegram"]["chat_id"]}&text={message}',
            timeout=10,
        )

    def save_exit(self: "RebalanceBot", reason: str = "") -> None:
        """Exits the bot"""
        logging.warning(reason)
        sys.exit(1)
