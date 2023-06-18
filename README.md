<h1 align=center>
    Welcome to the Spot rebalance bot for the Kraken Cryptocurrency Exchange 🐙
</h1>

<div align="center">

[![GitHub](https://badgen.net/badge/icon/github?icon=github&label)](https://github.com/btschwertfeger/Kraken-Rebalance-Bot)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-orange.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Generic badge](https://img.shields.io/badge/python-3.11+-blue.svg)](https://shields.io/)
![release](https://shields.io/github/release-date/btschwertfeger/kraken-rebalance-bot)
[![release](https://img.shields.io/pypi/v/kraken-rebalance-bot)](https://pypi.org/project/kraken-rebalance-bot/)
[![Typing](https://img.shields.io/badge/typing-mypy-informational)](https://mypy-lang.org/)
![ql-workflow](https://github.com/btschwertfeger/Kraken-Rebalance-Bot/actions/workflows/codeql.yaml/badge.svg)

</div>

> ⚠️ This is an unofficial trading bot that performs buys and sells
> on the Kraken cryptocurrency exchange using Python.

Backend to access the Kraken API: [python-kraken-sdk](https://github.com/btschwertfeger/python-kraken-sdk)

---

## 📌 Disclaimer

There is no guarantee that this software will work flawlessly at this or
later times. Of course, no responsibility is taken for possible profits or
losses. This software probably has some errors in it, so use it at your own
risk. Also no one should be motivated or tempted to invest assets in
speculative forms of investment. By using this software you release the
author(s) from any liability regarding the use of this software.

It is not certain that this software will ever lead to profits.

---

## 📝 The Strategy

This algorithm can buy and sell one or more Spot assets without leverage.

The goal is to hold a certain amount of each base currency so that, for
example, there is always about $1000 worth of BTC in the portfolio. If
the price of Bitcoin increases so that there is now $1050 worth of
Bitcoin in the portfolio, the excess $50 is sold. If the price of
Bitcoin falls, so that the Bitcoin in the portfolio are only worth $950,
the algorithm buys Bitcoin, to hold a value of about $1000 in Bitcoin
in the portfolio again.

The algorithm checks the price range every 6 hours by default. The
margin, from how many percent price difference the algorithm becomes
active, can also be adjusted.

Actions can be logged on the command-line using the logging module with
active INFO-level and can also be sent to a telegram bot.

---

## ⚙️ Quick start and configuration

### 0. Check the source code of this algorithm on GitHub and read the README.md carefully

- https://github.com/btschwertfeger/Kraken-Rebalance-Bot

### 1. Install the Python module:

```bash
python3 -m pip install kraken-rebalance-bot
```

### 2. Register at Kraken and generate API keys with trading access:

- https://www.kraken.com/u/security/api

### 3. (optional) Create a Telegram Bot to get notified when the algorithm takes action

1. Create a bot using <a href="https://t.me/BotFather" target="_blank">@BotFather</a>
2. Write down/remember the token
3. Start <a href="https://t.me/RawDataBot" target="_blank">@RawDataBot</a>
   and write down your personal `chat_id`

### 4. Setup the configuration and start the algorithm

An example configuration can be found in `example_config.json` and looks like
this:

```json
{
  "base_currency": ["ETH", "XBT"],    # base asset(s) to maintain
  "quote_currency": ["USD", "USD"],   # quote asset(s) to trade with
  "target_quantity": [500, 500],      # how many of the base to hold (value in quote)
  "quote_to_maintain": [200, 200],    # freezed quote
  "margin": [0.035, 0.035],           # buy/sell threshold
  "lowest_buy_price": [1000, 15000],  # don't buy below this price
  "times": ["06:00", "18:00"],        # has no effect if use_build_in_scheduler is true
  "use_build_in_scheduler": false,    # if set to false, the script will only run once
  "demo": true,                       # set to false to enable trading
  "telegram": {                       # optional to get notified via telegram
      "token": "telegram-bot-token",
      "chat_id": "your-telegram-chat-id"
  }
}
```

In the following a minimal working example is shown that uses this strategy
to hold a `target_quantity` of $500 of ETH and $500 worth of XBT (as in the
example config above). Both are traded against USD. The `demo` key must be
set to `False` to enable the trading functionality. Of course, this also works
with only one asset, too.

```bash
rebalance \
  --api-key "your-kraken-api-key-here" \
  --secret-key "secret-key-here" \
  --config config.json
```

Note: If `use_build_in_scheduler` is enabled, there will be no output until
the time is one of `times`.

---

## 📖 Configuration

| Key                      | Type                             | Description                                                                                                                                                             |
| ------------------------ | -------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `base_currency`          | `list[str]`                      | List of base currencies to trade and hold.                                                                                                                              |
| `quote_currency`         | `list[str]`                      | List of quote currencies to trade the base currency with.                                                                                                               |
| `target_quantity`        | `list[float] \| list[int]`       | Defines how much of a base currency should be held. This value is the worth of the base currency in quote currency.                                                     |
| `quote_to_maintain`      | `list[float] \| list[int]`       | How much of quote currency should not be touched in the portfolio.                                                                                                      |
| `margin`                 | `list[float]`                    | Rebalance levels e.g. 0.035 = 3.5%: at a change of 3.5% the algorithm will buy or sell the missing/surplus quantity                                                     |
| `lowest_buy_price`       | `list[float]`                    | (optional) The bot will not buy if the price falls below this price to avoid catching a falling knife. Acts Kind of stop loss, but without selling.                     |
| `times`                  | `list[str]`                      | (optional, default: `['00:00', '06:00', '12:00', '18:00']`) At which time the bot should check the balances.                                                            |
| `use_build_in_scheduler` | `bool`                           | (optional, default: `False`) Checks the balances once and exits if set to False. Otherwise the program will run forever and check the balances at the specified `times` |
| `demo`                   | `bool`                           | Trade or not sample trade output. Set to True if you know what this algorithm does.                                                                                     |
| `telegram`               | `{'chat_id': str, 'token': str}` | (optional) Specify token and chat id to get notified when the bot does something.                                                                                       |

If `use_build_in_scheduler` is set to `false`, the program is executed once
and ends after the iteration over all assets. This offers the possibility to
create own scripts, which execute this algorithm at individual times
(e.g. using <a href="https://wiki.ubuntuusers.de/Cron/" target="_blank">cron</a>).

---

## 📍 Notes

- Make sure to always have enough quote currency in your Kraken portfolio. Too
  low `target_quantity` values can cause the bot not to trade or even crash.
  Therefore, pay attention to the <a href="https://support.kraken.com/hc/en-us/articles/360050845612-Minimum-order-size-volume-for-trading-and-decimal-precision-for-residents-of-Japan-" target="_blank">minimum order sizes</a>.

**Example situation**:

- minimal order size of ETH is 0.01
- price of ETH: $1300
- `margin` is set to 0.04
- `target_quantity` is 200
- what will happen:

  - If your actual holdings of ETH is $192 the bot tries to buy Ethereum
    with a volume of $8 because $200 - $200 \* 0.04 will trigger the buy
    order. But the minimum order size of Ethereum is 0.01 ETH
    (see <a href="https://support.kraken.com/hc/en-us/articles/360050845612-Minimum-order-size-volume-for-trading-and-decimal-precision-for-residents-of-Japan-" target="_blank">here</a>),
    and with a price of $1300 => 0.01 ETH equals $13 so: $13 < $8 will
    raise an error.
  - So make sure that the minimum order sizes of the respective assets
    are consistent with the `margin` value and the `target_quantity`.
    The example would work if the `targe_quantity` is set to 500,
    because $500 _ 0.04 = $20 which is larger than $1300 _ 0.01 = $13.
  - Also make sure that there is enough quote currency, otherwise the
    bot cannot buy anything.

- This strategy is one of the simplest and most basic approaches for trading
  cryptocurrencies. For this reason, it should be noted here that this does not
  necessarily lead to profits. Before running such an algorithm, everyone
  should be clear about what products are being traded, what these products are
  for in the first place, and what makes them valuable. Even the best companies,
  stocks, materials, and also cryptocurrencies can become worthless from one day
  to the next, so everyone should do their own research and make their decisions
  based on these results.

- It has been decided here not to present any material regarding the profitability
  of this algorithm, as this could lead you to make your decisions based on my
  successes and failures. What works once or over a long period of time does not
  necessarily work in the future. But please let me know what you think about this
  basic algorithm and what could be improved.

- For any problems or suggestions - please open an issue.

---

## 🆕 Contributions

… are welcome!

## 🔭 References

- https://python-kraken-sdk.readthedocs.io/en/stable
