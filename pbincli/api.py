import requests
from pbincli.utils import json_encode

class PrivateBin:
    def __init__(self, server, proxy=None):
        self.server = server
        self.headers = {'X-Requested-With': 'JSONHttpRequest'}
        if proxy:
            self.proxy = {proxy.split('://')[0]: proxy}
        else:
            self.proxy = {}


    def post(self, request):
        r = requests.post(url = self.server, headers = self.headers, proxies = self.proxy, data = request)
        return r.text


    def get(self, request):
        url = self.server + "?" + request
        r = requests.get(url = url, headers = self.headers, proxies = self.proxy)
        return r.text


    def delete(self, pasteid, token):
        request = json_encode({'pasteid':pasteid,'deletetoken':token})
        r = requests.post(url = self.server, headers = self.headers, proxies = self.proxy, data = request)
        return r.text
