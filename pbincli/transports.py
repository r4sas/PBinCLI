import requests
import pbincli.settings

class privatebin(object):
    def __init__(self):
        self.server = pbincli.settings.server
        self.headers = {'X-Requested-With': 'JSONHttpRequest'}

        if pbincli.settings.useproxy:
            self.proxies = pbincli.settings.proxies
        else:
            self.proxies = {}

    def post(self, request):
        r = requests.post(url = self.server, headers = self.headers, proxies = self.proxies, data = request)
        return r.text


    def get(self, request):
        url = self.server + "?" + request
        r = requests.get(url = url, headers = self.headers, proxies = self.proxies)
        return r.text


    def delete(self, pasteid, token):
        request = {'pasteid':pasteid,'deletetoken':token}
        r = requests.post(url = self.server, headers = self.headers, proxies = self.proxies, data = request)
        return r.text
