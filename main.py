import time
import os 
from KrakenBot import *
import math
import sys
from datetime import date, datetime

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

FREQUENCY_D=15              #DAYS
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
MODE='proportion'


# Proprtions are in %
pairs = {'ADAUSD':33, 'XETHZUSD':34, 'DOTUSD':33}

check_sum = 0
for key, val in pairs.items(): check_sum += val

if check_sum != 100:
    print('Assets proportions are not correct!')
    sys.exit(0)


today = datetime(2021, 12, 30, 15, 11, 11, 0)
future = datetime(2021, 12, 30, 15, 50, 13, 345)
delta = future - today


# MAIN LOOP
while True:

    start = datetime.now()

    now = datetime.now()
    while (datetime.now()-start).seconds < FREQUENCY_S:
        time.sleep(MINUTE)
        now = datetime.now()
        print((now-start).seconds)
        

    print('New contribution period')
    # print((now-start).days)