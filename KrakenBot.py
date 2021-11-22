import requests
import urllib.parse
import hashlib
import hmac
import base64
import time
from requests.models import parse_header_links

class KrakenBot:

    def __init__(self, api_url, api_key, api_sec):
        self.api_url=api_url
        self.api_key=api_key
        self.api_sec=api_sec

    def dollar_cost_average(self):
        
        pass

    def get_balance(self, token=None):
        resp = self.kraken_request('/0/private/Balance', {
        "nonce": str(int(1000*time.time()))
        }, self.api_key, self.api_sec)

        if token==None:
            return resp.json()['result']
        else:
            try:
                return float(resp.json()['result'][token])
            except:
                print("This token does not exists!")

    def buy_pair(self, pair, ordertype, volume, price=None):
        if volume < self.order_min(pair):
            print("Volume is too low!")
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
            
                return resp.json()
        return 1

    def sell_pair(self, pair, ordertype, volume):

        if volume < self.order_min(pair):
            print("Volume is too low!")
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

    def order_min(self, pair):
        resp = requests.get(self.api_url+'/0/public/AssetPairs?pair='+pair)

        return float(resp.json()['result'][pair]['ordermin'])

    def get_price(self, pair, type='ask'):

        resp = requests.get(self.api_url+'/0/public/Ticker?pair='+pair)
        price = float(resp.json()['result'][pair][type[0]][0])

        return price

    def stake(self, asset, amount=None):
        asset_amount = self.get_balance(asset)
        method = self.get_staking_info(asset)['method']

        resp = self.kraken_request('/0/private/Stake', {
            "nonce": str(int(1000*time.time())),
            "asset": asset,
            "amount": asset_amount,
            "method": method
        }, self.api_key, self.api_sec)

        return resp.json()

    def unstake(self, asset):
        
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

    def get_staked_assets_balance(self):
        pass

    def get_staking_info(self, asset):
        resp = self.kraken_request('/0/private/Staking/Assets', {
        "nonce": str(int(1000*time.time()))
        }, self.api_key, self.api_sec)

        resp = resp.json()['result']

        for i in range(len(resp)):
            if resp[i]['asset'] == asset:
                return resp[i]

        return 1


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