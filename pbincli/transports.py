import requests
import pbincli.settings

class privatebin(object):
    def __init__(self):
        if args.server:
            self.server = args.server
        else:
            self.server = pbincli.settings.server

        self.headers = {'X-Requested-With': 'JSONHttpRequest'}

        if args.proxy:
            self.proxies = {args.proxy.split('://')[0]: args.proxy}
        elif pbincli.settings.useproxy:
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
