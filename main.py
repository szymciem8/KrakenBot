import time
import os 
from KrakenBot import *
import math
import sys
from datetime import date, datetime
import pickle

DOLLAR = 4.16

#Number of buy transactions per year
N_OF_BUYS=12

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

pairs = ['ADAUSD', 'XETHZUSD', 'DOTUSD']

kraken_bot = KrakenBot(api_url, api_key, api_sec)

MINUTE=60
HOUR=MINUTE*60
DAY=HOUR*24

FREQUENCY_D=30              #DAYS
FREQUENCY_H=FREQUENCY_D*24  #HOURS
FREQUENCY_M=FREQUENCY_H*60  #MINUTES
FREQUENCY_S=FREQUENCY_H*60  #SECONDS
CONTRIBUTION=40             #DOLLARS

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
pairs = {'ADAUSD':33, 'XETHZUSD':34, 'DOTUSD':33}

check_sum = 0
for key, val in pairs.items(): check_sum += val

if check_sum != 100:
    print('Assets proportions are not correct!')
    sys.exit(0)


contributions = {}

for key, val in pairs.items():
    contrib = (val * period_contribution)/100

    minimum_order = kraken_bot.order_min(key) * kraken_bot.get_price(key)
    print(minimum_order)
    if contrib < minimum_order:
        contrib = minimum_order

    contributions[key] = contrib

# print(contributions)

staked_assets = ['ADA', 'DOT']

today = datetime(2021, 12, 30, 15, 11, 11, 0)
future = datetime(2021, 12, 30, 15, 50, 13, 345)
delta = future - today

print('Bot has started...')

try:
    with open(r'start.pickle', 'rb') as start_file:
        start = pickle.load(start_file)
except:
    print('Pickle file does not exist.')
    print('Creating new one.')
    # Save with pickle
    start = datetime.now()
    with open(r'start.pickle', 'wb') as start_file:
        pickle.dump(start, start_file)

# MAIN LOOP
while True:

    now = datetime.now()
    while (datetime.now()-start).seconds < 10:
        #time.sleep(MINUTE) 
        now = datetime.now()
        #print((now-start).seconds)
    
    print(now)
    print('--------------------------------')
    # Make contribution
    print('Buying assets: ')
    for pair, value in pairs.items():
        if kraken_bot.get_balance('ZUSD') < value:
            print('Bying', pair, "failed!")
        else:
            print('Bought pair:', pair, value)
            # kraken_bot.buy_pair(pair, 'market', contributions[pair])

    # Stake available assets
    for asset in staked_assets:
        available_amount = kraken_bot.get_balance(asset)

        if available_amount == 0:
            print('Staking', asset, 'failed!')
        else:
            kraken_bot.stake(asset, available_amount)
            print('Staked', asset, available_amount)

    print('New contribution has been made')
    print('--------------------------------\n\n')

    start = datetime.now()
    with open(r'start.pickle', 'wb') as start_file:
        pickle.dump(start, start_file)