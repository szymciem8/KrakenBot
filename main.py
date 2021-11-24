import time
import os 
from KrakenBot import *
import math
import sys
from datetime import datetime
import pickle
import logging


# Logging
format  = '%(asctime)s-%(process)d-%(levelname)s-%(message)s'
logging.basicConfig(filename='logs/kraken_bot_log.log', filemode='a', format=format, level=logging.INFO)

# DIFFERENT APPROACH
# create two variables: frequency of buys, price per buy
# and dictionary: set of assets with given proportions
# if proporion * price per buy < minimum order: 
#       give error message
#       1, Increase the value of that asset.
#       2. Change the proportion,
#       3. Increase price per buy for all assets. 
# 
# Keep in mind that min order can change in the future. 
# If that happens algorithm should act accordingly to given rule. 

#  Read Kraken API key and secret stored in environment variables

api_url = "https://api.kraken.com"
api_key = os.environ['KRAKEN_KEY']
api_sec = os.environ['KRAKEN_SEC']

kraken_bot = KrakenBot(api_url, api_key, api_sec)

# Time constants
MINUTE=60
HOUR=MINUTE*60
DAY=HOUR*24

FREQUENCY_D=30              #DAYS
FREQUENCY_H=FREQUENCY_D*24  #HOURS
FREQUENCY_M=FREQUENCY_H*60  #MINUTES
FREQUENCY_S=FREQUENCY_H*60  #SECONDS
CONTRIBUTION=40             #DOLLARS

# Base currency
BASE_CURRENCY='ZUSD'

# If some asset's minimum order price happen to be higher than minimum 
# order price, algorithm will act accordingly to the MODE

# Availabe MODEs
# 1. "proportion" - increases contributions of other assets so that 
# the overall proportion of each stays the same. 
# 2. "min_order" - increases value of the given asset to value of 
# minimum order. 
# 3. "skip" - skip given asset
MODE='min_order'

# Value of contribution each period
period_contribution = 40

# Proprtions are in %
pairs = {'XETHZUSD':36, 'ADAUSD':22,  'DOTUSD':22, 'ALGOUSD':10, 'KSMUSD':10}
staked_assets = ['ADA', 'DOT', 'KSM', 'ALGO']

check_sum = 0
for key, val in pairs.items(): check_sum += val

if check_sum != 100:
    logging.info('Assets proportions are not correct!')
    sys.exit(0)

contributions = kraken_bot.check_contrib_values(pairs)

try:
    with open(r'start.pickle', 'rb') as start_file:
        start = pickle.load(start_file)
except:
    logging.info('Pickle file does not exist.')
    logging.info('Creating new one.')
    # Save with pickle
    start = datetime.now()
    with open(r'start.pickle', 'wb') as start_file:
        pickle.dump(start, start_file)

logging.info('Bot has started...')
# MAIN LOOP
while True:

    now = datetime.now()
    while (datetime.now()-start).seconds < 10:
        #time.sleep(MINUTE) 
        now = datetime.now()
        #logging.info((now-start).seconds)
    
    logging.info(now)
    logging.info('--------------------------------')
    # Make contribution
    logging.info('Buying assets')
    for pair, value in contributions.items():
        if kraken_bot.get_balance('ZUSD') < value:
            logging.warning(f'Low balance! Bying {pair} "failed.')
        else:
            # kraken_bot.buy_pair(pair, 'market', contributions[pair])
            logging.info(f'Bought pair: {pair}, \t{value}\t->\t{round(value*kraken_bot.get_price(pair),2)}')

    # Stake available assets

    logging.info('Staking assets')
    for asset in staked_assets:
        available_amount = kraken_bot.get_balance(asset)

        if available_amount == 0:
            logging.warning(f'Low balance! Staking {asset} failed.')
        else:
            kraken_bot.stake(asset, available_amount)
            logging.info(f'Staked {available_amount} of {asset}')

    logging.info('New contribution has been made')
    logging.info('--------------------------------\n\n')

    start = datetime.now()
    with open(r'start.pickle', 'wb') as start_file:
        pickle.dump(start, start_file)