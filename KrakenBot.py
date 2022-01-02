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
from datetime import datetime

# Time constants
MINUTE=60
HOUR=MINUTE*60
DAY=HOUR*24

MONEY_INVESTED_PATH = path = os.path.join(os.path.dirname(__file__), 'data/money_invested.pickle')
LOGS_PATH = os.path.join(os.path.dirname(__file__), 'logs/kraken_bot_log.log')

format  = '%(asctime)s-%(process)d-%(levelname)s-%(message)s'
logging.basicConfig(filename=LOGS_PATH, filemode='a', format=format, level=logging.INFO)

class KrakenBot:

    def __init__(self, api_url, api_key, api_sec):
        self.BASE_CURRENCY='ZUSD'

        self.api_url=api_url
        self.api_key=api_key
        self.api_sec=api_sec

        if os.path.exists(MONEY_INVESTED_PATH):
            with open(MONEY_INVESTED_PATH, 'rb') as file:
                self.money_invested = pickle.load(file)
                print('file')
        else:
            self.money_invested=0
            print('no file')

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
        }, self.api_key, self.api_sec).json()

        balance = {}
        if token==None:
            # Return all
            return resp['result']
        elif token=='staked':
            # Return staked
            for asset, volume in resp['result'].items():
                if '.S' in asset:
                    balance[asset] = volume
            return balance
        elif token=='unstaked':
            # Return unstaked
            for asset, volume in resp['result'].items():
                if '.S' not in asset:
                    balance[asset] = volume
            return balance
        else:
            try:
                # Return one token
                return float(resp['result'][token])
            except:
                logging.warning("This token does not exists!")
                return 1

    def asset_list(self, type='all'):

        if type=='all':
            return list(self.get_balance().keys())
        elif type=='staked':
            return list(self.get_balance('staked').keys())
        elif type=='unstaked':
            return list(self.get_balance('unstaked').keys())

    def get_price(self, pair, type='ask'):
        '''
        Get price of specified asset.
        '''
        resp = requests.get(self.api_url+'/0/public/Ticker?pair='+pair).json()
        price = float(resp['result'][pair][type[0]][0])

        return price

    def order_min(self, pair):
        '''
        Returns the minimum order value of give asset.
        '''
        resp = requests.get(self.api_url+'/0/public/AssetPairs?pair='+pair).json()
        return float(resp['result'][pair]['ordermin'])

    def dec_places(self, pair):
        '''
        Returns maximum number of decimal places of given asset.
        '''
        resp = requests.get(self.api_url+'/0/public/AssetPairs?pair='+pair).json()
        return int(resp['result'][pair]['lot_decimals'])

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
                }, self.api_key, self.api_sec).json()

                if not resp['error']:
                    self.money_invested += volume * self.get_price(pair)
                    logging.info(resp['error'])
                else:
                    logging.info(resp['result'])
            
                return resp
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
                }, self.api_key, self.api_sec).json()
            
                return resp
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
        elif isinstance(crypto, str):
            asset_amount = self.get_balance(crypto)

            print(crypto)
            method = self.get_staking_info(crypto)['method']

            resp = self.kraken_request('/0/private/Stake', {
                "nonce": str(int(1000*time.time())),
                "asset": crypto,
                "amount": asset_amount,
                "method": method
            }, self.api_key, self.api_sec).json()

            return resp

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
        }, self.api_key, self.api_sec).json()

        return resp

    def get_staking_info(self, asset):
        '''
        Get staking info of given asset.
        '''
        resp = self.kraken_request('/0/private/Staking/Assets', {
        "nonce": str(int(1000*time.time()))
        }, self.api_key, self.api_sec).json()

        for i in range(len(resp)):
            print(resp['result'][i])
            if resp['result'][i]['asset'] == asset:
                return resp['result'][i]
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
        if os.path.exists(path):
            with open(path, 'rb') as file:
                start = pickle.load(file)
            logging.info('Reading last cotribution date...')
            existed=True
        else:
            logging.info('Pickle file does not exist.')
            logging.info('Creating new one.')
            # Save with pickle
            start = datetime.now()
            with open(path, 'wb') as file:
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
                #self.buy_pair(pair, 'market', contributions[pair])
                logging.info(f'Bought pair: {pair} {value}->{round(value*self.get_price(pair),2)}')
    
        with open(MONEY_INVESTED_PATH, 'wb') as file:
            pickle.dump(self.money_invested, file)

    def get_profit(self, pairs, type='overall'):
        '''
        Calculates overall profit or just for given asset. 
        '''
        if type == 'overall':
            investment_value = 0
            balance = self.get_balance()

            for pair, percent in pairs.items():
                price = self.get_price(pair)

                if price is not None:
                    # pair = self.get_pair_info(asset, 'USD')
                    if 'ZUSD' in pair:
                        volume = balance[pair[:-4]]
                    elif 'USD':
                        volume = balance[pair[:-3]]
                    investment_value += float(volume) * self.get_price(pair)

            profit = investment_value/self.money_invested
            return profit

    def expected_staking_income(self, timeframe='month'):
        staked_assets = self.get_balance('staked')
        expected_income = 0

        for asset, volume in staked_assets.items():
            percentage_yield = self.get_staking_info(asset[:-2])['rewards']['reward']
            expected_income += volume * self.get_price(asset) * percentage_yield/100

        return expected_income


    def get_pair_info(self, asset, base, info_type='pair_name'):
        altname = asset + base

        resp = requests.get('https://api.kraken.com/0/public/AssetPairs').json()

        for key, dict in resp['result'].items():
            if dict['altname'] == altname:
                if info_type == 'pair_name':
                    return dict['base']+dict['quote']
                else:
                    return dict[info_type]

    def dollar_cost_average(self):
        pass

    def sell_all_assets(self):
        # 1. All at once
        # 2. Gradually
        pass 

    def unstake_all(self):
        pass

    def trading_strategy(self):
        pass

    def ai_trading(self):
        pass