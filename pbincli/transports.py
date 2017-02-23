import requests


class privatebin(object):
    def __init__(self):
        self.proxies = {'http': 'http://127.0.0.1:4444'}
        self.server = 'http://paste.r4sas.i2p/'
        self.headers = {'X-Requested-With': 'JSONHttpRequest'}


    def post(self, request):
        r = requests.post(url=self.server, headers=self.headers, proxies=self.proxies, data=request)
        return r.text, self.server


    def get(self, request):
        url = self.server + "?" + request
        r = requests.get(url=url, headers=self.headers, proxies=self.proxies)
        return r.text


    def delete(self, pasteid, token):
        request = {'pasteid':pasteid,'deletetoken':token}
        r = requests.post(url=self.server, headers=self.headers, proxies=self.proxies, data=request)
        return r.text
