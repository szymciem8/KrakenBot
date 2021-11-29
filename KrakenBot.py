import requests
import urllib.parse
import hashlib
import hmac
import base64
import time
from requests.models import parse_header_links
import logging
import os
import pickle
import datetime

# Time constants
MINUTE=60
HOUR=MINUTE*60
DAY=HOUR*24

MONEY_INVESTED_PATH = path = os.path.join(os.path.dirname(__file__), 'data/money_invested.pickle')
START_TIME_PATH = os.path.join(os.path.dirname(__file__), 'logs/kraken_bot_log.log')

format  = '%(asctime)s-%(process)d-%(levelname)s-%(message)s'
logging.basicConfig(filename=START_TIME_PATH, filemode='a', format=format, level=logging.INFO)

class KrakenBot:

    def __init__(self, api_url, api_key, api_sec):
        self.BASE_CURRENCY='ZUSD'
   
        self.api_url=api_url
        self.api_key=api_key
        self.api_sec=api_sec

        if os.path.exists(MONEY_INVESTED_PATH):
            with open(MONEY_INVESTED_PATH, 'wb') as file:
                self.money_invested = pickle.load(file)
        else:
            self.money_invested=0

    def get_kraken_signature(self, urlpath, data, secret):
        postdata = urllib.parse.urlencode(data)
        encoded = (str(data['nonce']) + postdata).encode()
        message = urlpath.encode() + hashlib.sha256(encoded).digest()

        mac = hmac.new(base64.b64decode(secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(mac.digest())
        return sigdigest.decode()

    # Attaches auth headers and returns results of a POST request
    def kraken_request(self, uri_path, data, api_key, api_sec):
        headers = {}
        headers['API-Key'] = api_key
        # get_kraken_signature() as defined in the 'Authentication' section
        headers['API-Sign'] = self.get_kraken_signature(uri_path, data, api_sec)             
        req = requests.post((self.api_url + uri_path), headers=headers, data=data)
        return req

    def get_balance(self, token=None):
        '''
        Returns balance of all assets or the one specified.
        '''
        resp = self.kraken_request('/0/private/Balance', {
        "nonce": str(int(1000*time.time()))
        }, self.api_key, self.api_sec)

        if token==None:
            return resp.json()['result']
        else:
            try:
                return float(resp.json()['result'][token])
            except:
                logging.warning("This token does not exists!")

    def get_price(self, pair, type='ask'):
        '''
        Get price of specified asset.
        '''
        resp = requests.get(self.api_url+'/0/public/Ticker?pair='+pair)
        price = float(resp.json()['result'][pair][type[0]][0])

        return price

    def order_min(self, pair):
        '''
        Returns the minimum order value of give asset.
        '''
        resp = requests.get(self.api_url+'/0/public/AssetPairs?pair='+pair)
        return float(resp.json()['result'][pair]['ordermin'])

    def dec_places(self, pair):
        '''
        Returns maximum number of decimal places of given asset.
        '''
        resp = requests.get(self.api_url+'/0/public/AssetPairs?pair='+pair)
        return int(resp.json()['result'][pair]['lot_decimals'])

    def buy_pair(self, pair, ordertype, volume, price=None):
        '''
        Buy given asset with specifed settings. 
        '''
        if volume < self.order_min(pair):
            logging.warning("Volume is too low!")
            return 1
        else:
            if ordertype=='market':
                resp = self.kraken_request('/0/private/AddOrder', {
                    "nonce": str(int(1000*time.time())),
                    "ordertype": ordertype,
                    "type": "buy",
                    "volume": volume,
                    "pair": pair
                }, self.api_key, self.api_sec)

                if not resp.json()['error']:
                    self.money_invested += volume * self.get_price(pair)
            
                return resp.json()
        return 1

    def sell_pair(self, pair, ordertype, volume):
        '''
        Sell given asset with specified settings.
        '''
        if volume < self.order_min(pair):
            logging.warning("Volume is too low!")
            return 1
        else:
            if ordertype=='market':
                resp = self.kraken_request('/0/private/AddOrder', {
                    "nonce": str(int(1000*time.time())),
                    "ordertype": ordertype,
                    "type": "sell",
                    "volume": volume,
                    "pair": pair
                }, self.api_key, self.api_sec)
            
                return resp.json()
        return 1

    def stake(self, crypto=None, amount=None):
        '''
        Stake list of assets or just one asset.
        '''
        if isinstance(crypto, list):
            logging.info('Staking assets')
            for asset in crypto:
                available_amount = self.get_balance(asset)

                if available_amount == 0:
                    logging.warning(f'Low balance! Staking {asset} failed.')
                else:
                    self.stake(asset, available_amount)
                    logging.info(f'Staked {available_amount} of {asset}')
        else:
            asset_amount = self.get_balance(crypto)
            method = self.get_staking_info(crypto)['method']

            resp = self.kraken_request('/0/private/Stake', {
                "nonce": str(int(1000*time.time())),
                "asset": crypto,
                "amount": asset_amount,
                "method": method
            }, self.api_key, self.api_sec)

            return resp.json()

    def unstake(self, asset):
        '''
        Unstake given asset.
        '''
        method = self.get_staking_info(asset)['method']

        asset += ".S"
        asset_amount = self.get_balance(asset)
        
        resp = self.kraken_request('/0/private/Unstake', {
            "nonce": str(int(1000*time.time())),
            "asset": asset,
            "amount": asset_amount,
            "method": method
        }, self.api_key, self.api_sec)

        return resp.json()

    def get_staking_info(self, asset):
        '''
        Get staking info of given asset.
        '''
        resp = self.kraken_request('/0/private/Staking/Assets', {
        "nonce": str(int(1000*time.time()))
        }, self.api_key, self.api_sec)

        resp = resp.json()['result']

        for i in range(len(resp)):
            if resp[i]['asset'] == asset:
                return resp[i]

        return 1

    def check_contrib_values(self, pairs, contrib_per_period, mode='min_order'):
        '''
        Check if contribution values of each asset or higher than minimum 
        order value. If not, change them accordigly to specified mode. 
        '''
        contributions = {}
        for pair, percentage in pairs.items():
            contrib = (percentage * contrib_per_period)/100

            minimum_order = self.order_min(pair)
            price=self.get_price(pair)
            logging.info(f'Minimum order volume: {pair}: {minimum_order}')

            if contrib/price < minimum_order:
                if mode=='min_order':
                    contributions[pair] = round(minimum_order, self.dec_places(pair))
                    logging.info(f'Updated {pair} contribution to {contributions[pair]}')
                elif mode == 'keep_proportion':
                    contrib_per_period = (100*minimum_order*price)/percentage
                    logging.info(f'Updated contribution to: {contrib_per_period}')
                    return self.check_contrib_values(pairs)
                elif mode == 'skip':
                    del percentage
                    logging.info(f'Deleted pair {pair}')
            else:
                contributions[pair] = round(contrib/price, self.dec_places(pair))

        return contributions

    def get_start_time(self):
        '''
        Read start time of the bot from pickle file, if it does not exist, create one. 
        '''
        path = os.path.join(os.path.dirname(__file__), 'start.pickle')
        if os.path.exists(START_TIME_PATH):
            with open(START_TIME_PATH, 'rb') as file:
                start = pickle.load(file)
            logging.info('Reading last cotribution date...')
            existed=True
        else:
            logging.info('Pickle file does not exist.')
            logging.info('Creating new one.')
            # Save with pickle
            start = datetime.now()
            with open(START_TIME_PATH, 'wb') as file:
                pickle.dump(start, file)
            existed=False

        return start, existed

    def make_contribution(self, pairs, contrib_per_period):
        '''
        Make regular contribution of asset. 
        '''
        contributions = self.check_contrib_values(pairs, contrib_per_period)
        logging.info('Buying assets')
        for pair, value in contributions.items():
            if self.get_balance('ZUSD') < value:
                logging.warning(f'Low balance! Bying {pair} "failed.')
            else:
                # kraken_bot.buy_pair(pair, 'market', contributions[pair])
                with open(MONEY_INVESTED_PATH, 'wb') as file:
                    pickle.dump(self.money_invested, file)

                logging.info(f'Bought pair: {pair} {value}->{round(value*self.get_price(pair),2)}')
    
    def get_profit(type='overall'):
        # profit = value_of_assets/value_of_money_invested
        # What if something is sold?
        pass

    def get_staked_assets_balance(self):
        pass

    def expected_staking_profit(self, timeframe='month'):
        pass

    def dollar_cost_average(self):
        pass