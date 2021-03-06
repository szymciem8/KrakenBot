import time
import os 
from KrakenBot import *
import sys
from datetime import datetime
import pickle
import logging

FREQUENCY_D=31              #DAYS
FREQUENCY_H=FREQUENCY_D*24  #HOURS
FREQUENCY_M=FREQUENCY_H*60  #MINUTES
FREQUENCY_S=FREQUENCY_H*60  #SECONDS

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
contrib_per_period = 60

# Paris with proportions. Proprtions are in %
pairs = {'XETHZUSD':22, 
         'ADAUSD':20, 
         'SOLUSD':20, 
         'DOTUSD':20, 
         'ALGOUSD':9, 
         'KSMUSD':9}

staked_assets = ['ADA', 'SOL', 'DOT', 'KSM', 'ALGO']

check_sum = 0
for key, val in pairs.items(): check_sum += val
if check_sum != 100:
    logging.info('Assets proportions are not correct!')
    sys.exit(0)

print(kraken_bot.check_contrib_values(pairs, contrib_per_period, 'keep_proportion'))
resp = input('Press Enter to continue or Q to exit: ')

if resp.lower() == 'q':
    sys.exit()

logging.info('Bot has started...')
start, exists = kraken_bot.get_start_time()
if not exists:
    kraken_bot.make_contribution(pairs, contrib_per_period)
    time.sleep(MINUTE)
    kraken_bot.stake(staked_assets)

# MAIN LOOP
while True:

    now = datetime.now()
    while (datetime.now()-start).seconds < FREQUENCY_S:
        time.sleep(MINUTE) 
        now = datetime.now()
    
    # Make contribution
    kraken_bot.make_contribution(pairs, contrib_per_period)
    logging.info('New contribution has been made')

    time.sleep(MINUTE)

    # Stake available assets
    kraken_bot.stake(staked_assets)
    logging.info('Assets has been staked')
    
    start = datetime.now()
    with open(path, 'wb') as start_file:
        pickle.dump(start, start_file)