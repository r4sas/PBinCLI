import requests
import json
import urllib
from pprint import pprint
class privatebin(object):

    def __init__(self):
        self.proxies = {'http': 'http://127.0.0.1:4444'}
        self.server = 'http://paste.r4sas.i2p/'
        self.headers = {'X-Requested-With': 'JSONHttpRequest'}

    def post(self, data):
        r = requests.post(url=self.server, headers=self.headers, proxies=self.proxies, data=data)
        print(r.request)
        print(r.status_code)
        print(r.text) 
