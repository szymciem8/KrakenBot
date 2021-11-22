import time
import os 
from KrakenBot import *
import math

DOLLAR = 4.16

#Number of buy transactions per year
N_OF_BUYS=12

# Try to buy a given assset N_OF_BUYS per year 
# Price of assets changes
# If the calculated price is higher than minimum order price 
# change buying period so that money is spent over the year

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

# usd_balance = float(kraken_bot.get_balance()['USDT'])
usd_balance = 500
avg_cost_per_period = usd_balance/(N_OF_BUYS)
print(avg_cost_per_period)

print('balance', usd_balance, '$')

periodic_payment=0

for pair in pairs:
    token_price = kraken_bot.get_price(pair)
    min_token_price = kraken_bot.order_min(pair)*token_price

    periodic_payment += min_token_price
    print(pair, min_token_price, '$')

print(avg_cost_per_period-periodic_payment)
payment_period=usd_balance/periodic_payment
print(math.floor(payment_period))
