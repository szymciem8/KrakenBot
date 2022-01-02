import time
import os 
from KrakenBot import *
import sys
from datetime import datetime
import pickle
import logging

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

# Paris with proportions. Proprtions are in %
pairs = {'XETHZUSD':24, 
         'ADAUSD':22,
         'SOLUSD':22, 
         'DOTUSD':22, 
         'ALGOUSD':5, 
         'KSMUSD':5}

staked_assets = ['ADA', 'SOL', 'DOT', 'KSM', 'ALGO']

#kraken_bot.make_contribution(pairs, contrib_per_period)

# kraken_bot.buy_pair('SOLUSD', 'market', 0.02)

# TODO
# print(kraken_bot.get_price('SOLUSD'))
# print(kraken_bot.get_profit())
print(kraken_bot.get_profit(pairs))

# print(kraken_bot.get_pair_info('ETH', 'USD', 'pair_name'))

# kraken_bot.make_contribution(pairs, contrib_per_period)
# kraken_bot.stake(staked_assets)

# print(kraken_bot.get_staking_info('dfgd'))
# print(kraken_bot.get_balance('unstaked'))
# print(kraken_bot.get_balance('staked'))
