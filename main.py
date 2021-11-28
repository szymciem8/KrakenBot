import time
import os 
from KrakenBot import *
import sys
from datetime import datetime
import pickle
import logging

# Time constants
MINUTE=60
HOUR=MINUTE*60
DAY=HOUR*24

FREQUENCY_D=30              #DAYS
FREQUENCY_H=FREQUENCY_D*24  #HOURS
FREQUENCY_M=FREQUENCY_H*60  #MINUTES
FREQUENCY_S=FREQUENCY_H*60  #SECONDS
CONTRIBUTION=40             #DOLLARS

# Logging
format  = '%(asctime)s-%(process)d-%(levelname)s-%(message)s'
path = os.path.join(os.path.dirname(__file__), 'logs/kraken_bot_log.log')
logging.basicConfig(filename=path, filemode='a', format=format, level=logging.INFO)

# API
api_url = "https://api.kraken.com"
api_key = os.environ['KRAKEN_KEY']
api_sec = os.environ['KRAKEN_SEC']

kraken_bot = KrakenBot(api_url, api_key, api_sec)

# Value of contribution each period
contrib_per_period = 40

# Proprtions are in %
pairs = {'XETHZUSD':36, 'ADAUSD':22,  'DOTUSD':22, 'ALGOUSD':10, 'KSMUSD':10}
staked_assets = ['ADA', 'DOT', 'KSM', 'ALGO']

check_sum = 0
for key, val in pairs.items(): check_sum += val

if check_sum != 100:
    logging.info('Assets proportions are not correct!')
    sys.exit(0)

path = os.path.join(os.path.dirname(__file__), 'start.pickle')
if os.path.exists(path):
    with open(path, 'rb') as start_file:
        start = pickle.load(start_file)
    logging.info('Reading last cotribution date...')
else:
    logging.info('Pickle file does not exist.')
    logging.info('Creating new one.')
    # Save with pickle
    start = datetime.now()
    with open(path, 'wb') as start_file:
        pickle.dump(start, start_file)

    kraken_bot.buy_pair(pairs, contrib_per_period)
    time.sleep(MINUTE)
    kraken_bot.stake(staked_assets)

logging.info('Bot has started...')
# MAIN LOOP
while True:

    now = datetime.now()
    while (datetime.now()-start).seconds < 10:
        #time.sleep(MINUTE) 
        now = datetime.now()
    
    # Make contribution
    kraken_bot.make_contribution(pairs, contrib_per_period)

    # Stake available assets
    kraken_bot.stake(staked_assets)

    logging.info('New contribution has been made')

    start = datetime.now()
    with open(r'start.pickle', 'wb') as start_file:
        pickle.dump(start, start_file)