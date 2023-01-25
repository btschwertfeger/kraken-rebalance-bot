import os
import sys
import json
import traceback
import logging
from krakenRebalanceBot.bot import RebalanceBot

# set some logging info (optional)
logging.basicConfig(
    format='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S',
    level=logging.INFO
)

def main() -> None:
    '''Loads the API keys, config, and runs the bot'''

    key = os.getenv('API_KEY')
    secret = os.getenv('SECRET_KEY')
    if key is None or secret is None:
        logging.error('Key not found in specified file.')
        sys.exit(1)

    config = {
        'base_currency': [x for x in os.getenv('base_currency').split(',') if x != ''],
        'quote_currency': [x for x in os.getenv('quote_currency').split(',') if x != ''],
        'target_quantity': [float(x) for x in os.getenv('target_quantity').split(',') if x != ''],
        'quote_to_maintain': [float(x) for x in os.getenv('quote_to_maintain').split(',') if x != ''],
        'margin': [float(x) for x in os.getenv('margin').split(',')],
        'lowest_buy_price': [float(x) for x in os.getenv('lowest_buy_price').split(',') if x != ''],
        'times': os.getenv('times').split(','),
        'demo': os.getenv('demo', False),
        'use_build_in_sheduler': os.getenv('use_build_in_sheduler'),
        'telegram': {
            'token': os.getenv('TG_TOKEN'),
            'chat_id': os.getenv('TG_CHAT_ID')
        }
    }
    
    if config['telegram']['token'] is None \
        or not config['telegram']['chat_id'] is None:
        logging.warning('Not using telegram.')
    
    # instantiate the bot
    bot = RebalanceBot(key=key, secret=secret, config=config)
    
    try: # run the bot
        bot.run()
    except Exception as exc:
        logging.error(f'Bot encountered some exception: {exc} {traceback.format_exc()}')

if __name__ == '__main__': 
    main()
