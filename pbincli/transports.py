import requests
import json
import urllib
from pprint import pprint
class privatebin(object):

    def __init__(self):
        self.proxies = {'http': 'http://127.0.0.1:4444'}
        self.server = 'http://paste.r4sas.i2p/'
        self.headers = {'X-Requested-With': 'JSONHttpRequest'}

    def post(self, data, password):
        r = requests.post(url=self.server, headers=self.headers, proxies=self.proxies, data=data)
        print(r.text)
        result = json.loads(r.text)
        '''{"status":0,"id":"aaabbb","url":"\/?aaabbb","deletetoken":"aaabbbccc"}'''
        if result['status'] == 0:
            print("Paste uploaded!\nPasteID:\t{}\nPassword:\t{}\nDelete token:\t{}\n".format(result['id'], password.decode("UTF-8"), result['deletetoken']))
