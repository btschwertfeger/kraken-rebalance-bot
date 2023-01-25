import sys
import json
import traceback
import logging
from dotenv import dotenv_values

# set some logging info (optional)
logging.basicConfig(
    format='%(asctime)s %(module)s,line: %(lineno)d %(levelname)8s | %(message)s',
    datefmt='%Y/%m/%d %H:%M:%S',
    level=logging.INFO
)

try:
    from krakenRebalanceBot.bot import RebalanceBot
except ModuleNotFoundError:
    logging.info('USING LOCAL MODULE')
    import sys
    sys.path.append('/Users/benjamin/repositories/Trading/Kraken-Rebalance-Bot')
    from krakenRebalanceBot.bot import RebalanceBot

def main() -> None:
    '''Loads the API keys, config, and runs the bot'''
    try: # loading API keys
        env = dotenv_values('.env')
        key = env['API_KEY']
        secret = env['SECRET_KEY']

    except KeyError:
        logging.error('Key not found in specified file.')
        sys.exit(1)

    try:                
        # load telegram token and chat id (optional)
        tg_token = env['TG_TOKEN']
        tg_chat_id = env['TG_CHAT_ID']
    except KeyError:
        tg_token = None
        tg_chat_id = None
        logging.warning('Not using telegram.')

    try: # loading config file
        with open('config.json', 'rb') as json_file:
            config = json.load(json_file)

        config['telegram'] = {
            'token': tg_token,
            'chat_id': tg_chat_id
        }

    except FileNotFoundError:
        logging.error('Config file config.json not found!')
        sys.exit(1)
    
    # instantiate the bot
    bot = RebalanceBot(key=key, secret=secret, config=config)
    
    try: # run the bot
        bot.run()
    except Exception as exc:
        logging.error(f'Bot encountered some exception: {exc} {traceback.format_exc()}')

if __name__ == '__main__': 
    main()
