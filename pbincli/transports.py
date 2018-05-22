import requests
import pbincli.settings

class PrivateBin:
    def __init__(self, server = pbincli.settings.server, proxy = pbincli.settings.proxy, useproxy = pbincli.settings.useproxy):
        self.server = server
        self.headers = {'X-Requested-With': 'JSONHttpRequest'}
        if useproxy:
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
        request = {'pasteid':pasteid,'deletetoken':token}
        r = requests.post(url = self.server, headers = self.headers, proxies = self.proxy, data = request)
        return r.text
