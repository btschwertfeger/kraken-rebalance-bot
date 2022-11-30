import sys
import time
import logging
import schedule
import numpy as np
import requests
from kraken.spot.client import User, Market, Trade


class RebalanceBot():
    '''
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
                'use_build_in_sheduler': false, # optional    
            }
        )
        bot.run()
    '''

    TIMES = ['00:00', '06:00', '12:00', '18:00']

    def __init__(self, key: str, secret: str, config: dict):
        self.__market = Market()
        self.__trade = Trade(key=key, secret=secret)
        self.__user = User(key=key, secret=secret)
        
        self.__use_telegram = False
        self.__demo = True
        self.__config = config
        self.__check_config()
        
    def run(self) -> None:
        '''Runs the bot'''
        
        if self.__config.get('use_build_in_sheduler', False):
            for schedule_time in self.__config['times']:
                schedule.every().day.at(schedule_time).do(self.__check_balances)

            while True:
                schedule.run_pending()
                time.sleep(60)

        else: 
            self.__check_balances()
            sys.exit(0)

    def __check_balances(self) -> None:
        '''Checks if buy or sell order must be placed'''
        logging.info('Checking balances')

        for i, base_currency in enumerate(self.__config['base_currency']):
            quote_to_maintain = self.__config['quote_to_maintain'][i]
            target_quantity = self.__config['target_quantity'][i]
            quote_currency = self.__config['quote_currency'][i]
            margin = self.__config['margin'][i]

            available_balance_base = float(self.__user.get_balances(currency=base_currency)['available_balance'])
            available_balance_quote = float(self.__user.get_balances(currency=quote_currency)['available_balance'])

            ticker = self.__market.get_ticker(pair=f'{base_currency}{quote_currency}')
            symbol = list(ticker.keys())[0]
            value = available_balance_base * float(ticker[symbol]['c'][0])

            msg = f'\n👑 {symbol} Rebalance Bot'
            msg += f'\n├ Price: {float(ticker[symbol]["c"][0])} '
            msg += f'\n├ Available {base_currency} » {available_balance_base} ({value} {quote_currency} / {target_quantity} {quote_currency})'
            msg += f'\n└ Available {quote_currency} » {available_balance_quote}'
            logging.info(f'\n{msg}')

            rebalanced = False
            # check range is left
            if value <= target_quantity - target_quantity * margin: 
                # check if buy would not break quantity to maintain
                if available_balance_quote > quote_to_maintain + target_quantity - value: 
                    self.__rebalance(
                        symbol=symbol,
                        side='buy',
                        index=i,
                        available={
                            'base': available_balance_base, 
                            'quote': available_balance_quote
                        },
                        last_price=float(ticker[symbol]['c'][0])
                    )
                    rebalanced = True
                else:
                    msg = f'{symbol}: Not enough {quote_currency} to buy more {base_currency}. Noting changed.'
                    logging.info(msg)
            
            # check if new sell
            elif value >= target_quantity + target_quantity * margin:
                self.__rebalance(
                    symbol=symbol,
                    side='sell',
                    index=i,
                    available={ 
                        'base': available_balance_base, 
                        'quote': available_balance_quote
                    },
                    last_price=float(ticker[symbol]['c'[0]])
                )
                rebalanced = True
            if rebalanced:
                # wait to ensure that Krakens backend swallowed all requests
                # to ensure the fetched balances match the actual balances
                time.sleep(3)
                available_balance_base = float(self.__user.get_balances(currency=base_currency)['available_balance'])
                value = available_balance_base * float(self.__market.get_ticker(pair=symbol)[symbol]['c'][0])
                
                msg = f'👑 {symbol} Rebalance Bot updated values'
                msg += f'\n├ Available {base_currency} » {available_balance_base} ({value} {quote_currency} / {target_quantity} {quote_currency})'
                msg += f'\n└ Available {quote_currency} » {self.__user.get_balances(currency=quote_currency)["available_balance"]}'
                logging.info(f'\n{msg}')
            else:
                msg += f'\n... nothing changed.'
            
            self.send_to_telegram(message=msg)
            time.sleep(1)

    def __rebalance(self, symbol: str, side: str, index: int, available: dict, last_price: float) -> None:
        '''Places buy and sell orders'''
        msg = f'Rebalancing {symbol} ...'
        self.__new_message += f'\n\n{msg}'
        
        quote_volume = self.__config['target_quantity'][index] - (available['base'] * last_price)

        # get information about the symbol to calculate the buying or selling size
        symbol_data = self.__market.get_tradable_asset_pair(pair=symbol)[symbol]
        ordermin = float(symbol_data['ordermin'])

        base_factor = int(f'1{symbol_data["lot_decimals"]*str(0)}')
        if base_factor == 0: baseIncrementSize = int(symbol_data['lot_multiplier'])
        else: baseIncrementSize = float(int(symbol_data['lot_multiplier']) / base_factor)

        baseRoundVal = self.__get_decimal_round_value(baseIncrementSize)
        order_size =  self.__floor(abs(quote_volume) / float(last_price), baseRoundVal)
 
        if ordermin > order_size: 
            msg = '❌ Ordermin > order size. Please check if your symbols or asset pairs \
                minimum trade sizes match up with your target holdings, margins, and available quote balances. \
                \n- also see: https://support.kraken.com/hc/en-us/articles/360050845612-Minimum-order-size-volume-for-trading-and-decimal-precision-for-residents-of-Japan-\
                \n- and https://github.com/btschwertfeger/Kraken-Rebalance-Bot'
            self.send_to_telegram(message=msg)
            raise ValueError(msg)

        msg = f'✅ {side[0].upper()}{side[1:]} {order_size} {self.__config["base_currency"][index]} around {last_price} '
        msg += f'{self.__config["quote_currency"][index]} (volume: {quote_volume} {self.__config["quote_currency"][index]})'
        logging.info(msg)
        self.send_to_telegram(message=msg)

        if self.__demo: return 

        if side == 'buy': 
            response = self.__trade.create_order(
                ordertype='market',
                side='buy',
                pair=symbol,
                volume=order_size
            )
            logging.debug(f'Placed order response: {response}')

        if side == 'sell':
            response = self.__trade.create_order(
                ordertype='market',
                side='sell',
                pair=symbol,
                volume=order_size
            )
            logging.debug(f'Placed order response: {response}')

    def __floor(self, value: float, precision: int=0) -> float:
        ''' floor to precision '''
        return np.true_divide(np.floor(value * 10.0 ** precision), 10.0 ** precision)

    def __get_decimal_round_value(self, x: float) -> float:
        ''' returns the number on how often to multiply x by 10 to get x >= 1
        '''
        roundVal = 0
        while x < 1:
            x *= 10
            roundVal += 1
        return roundVal

    def __check_config(self) -> None:
        '''Checks the config for missing or wrong values'''
        # ___base_currency____
        if 'base_currency' in self.__config:
            if not isinstance(self.__config['base_currency'], list):
                raise ValueError('base_currency must be type List[str] in config.')
            if len(self.__config['base_currency']) == 0:
                raise ValueError('No pair(s) specified in config.')
            if len([pair for pair in self.__config['base_currency'] if not isinstance(pair, str)]) != 0:
                raise ValueError('Each pair in config must be type str.')
        else:
            raise ValueError('Missing base_currency in config file.')

        if 'quote_currency' in self.__config:
            if not isinstance(self.__config['quote_currency'], list):
                raise ValueError('quote_currency must be type List[str] in config.')
            if len(self.__config['quote_currency']) == 0:
                raise ValueError('No pair(s) specified in config.')
            if len([pair for pair in self.__config['quote_currency'] if not isinstance(pair, str)]) != 0:
                raise ValueError('Each pair in config must be type str.')
        else:
            raise ValueError('Missing quote_currency in config file.')

        # ___quantity____
        if 'target_quantity' in self.__config:
            if not isinstance(self.__config['target_quantity'], list): 
                raise ValueError('No quantity in config must be type List[float].')
            if len(self.__config['target_quantity']) == 0:
                raise ValueError('No quantity defined in config.')
            if len([q for q in self.__config['target_quantity'] if not isinstance(q, int) and not isinstance(q, int)]) != 0:
                raise ValueError('quantity must be type int or float in config.')
        else:
            raise ValueError('No quantity defined in config.')

        # ___QUOTE_TO_MAINTAIN____
        if 'quote_to_maintain' in self.__config:
            if not isinstance(self.__config['quote_to_maintain'], list):
                raise ValueError('No quote_to_maintain in config must be type List[float].')
            if len(self.__config['quote_to_maintain']) == 0:
                raise ValueError('No quote_to_maintain specified.')
            if len([q for q in self.__config['quote_to_maintain'] if not isinstance(q, float) and not isinstance(q, int)]) != 0:
                raise ValueError('quote_to_maintain must be type int or float in config.')
        else:
            raise ValueError('No quote_to_maintain defined in config.')
        
        # ___MARGIN___
        if 'margin' in self.__config:
            if not isinstance(self.__config['margin'], list):
                raise ValueError('margin should be type List[str].')
            if len([m for m in self.__config['margin'] if not isinstance(m, float) or m >= .99]) != 0:
                raise ValueError('Margin should be less than 0.99, e.g. 0.04 for a 4% rebalance.')
        else: 
            ValueError('No margin defined in config.')

         # ___MATCHING_PARAMETERS____
        if len(self.__config['base_currency']) != len(self.__config['target_quantity'])              \
            or len(self.__config['base_currency']) != len(self.__config['quote_currency'])            \
            or len(self.__config['base_currency']) != len(self.__config['margin'])            \
            or len(self.__config['base_currency']) != len(self.__config['quote_to_maintain']):
            raise ValueError('Lengths of: base_currency, quantity, margin and quote_to_maintain must be the same.')

        if 'times' in self.__config:
            if not isinstance(self.__config['times'], list) \
                or len([t for t in self.__config['times'] if not isinstance(t, str)]) != 0:
                raise ValueError('times must be type List[str] in config.')
        else:
            logging.warning('No times specfied in config. Default ["00:00", "06:00", "12:00", "18:00"] will be used.')
            self.__config['times'] = self.TIMES

        if 'telegram' in self.__config:
            if 'token' in self.__config['telegram'] and self.__config['telegram']['token'] \
                and 'chat_id' in self.__config['telegram'] and self.__config['telegram']['chat_id']:
                self.__use_telegram = True

        if 'demo' in self.__config and isinstance(self.__config['demo'], bool):
            self.__demo = self.__config['demo']
            logging.info('Demo mode active, not trading.')


    def send_to_telegram(self, message: str) -> None:
        '''Send a Message to telegram'''
        if not self.__use_telegram: return

        requests.post(
            f'https://api.telegram.org/bot{self.__config["telegram"]["token"]}/sendMessage?chat_id={self.__config["telegram"]["chat_id"]}&text={message}',
            timeout=10
        )

    def save_exit(self, reason: str='') -> None:
        '''Exits the bot'''
        logging.warning(reason)
        sys.exit(1)
