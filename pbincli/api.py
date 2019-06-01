import requests

class PrivateBin:
    def __init__(self, server, proxy=None):
        self.server = server
        self.__headers = {'X-Requested-With': 'JSONHttpRequest'}
        if proxy:
            self.__proxy = {proxy.split('://')[0]: proxy}
        else:
            self.__proxy = {}


    def post(self, request):
        return requests.post(
            url = self.server,
            headers = self.__headers,
            proxies = self.__proxy,
            data = request).json()


    def get(self, request):
        return requests.get(
            url = self.server + "?" + request,
            headers = self.__headers,
            proxies = self.__proxy).json()


    def delete(self, request):
        from pbincli.utils import json_encode
        return requests.post(
            url = self.server,
            headers = self.__headers,
            proxies = self.__proxy,
            data = request).json()


    def getVersion(self, context):
        jsonldSchema = requests.get(
            url = self.server + context,
            proxies = self.__proxy).json()
        return jsonldSchema['@context']['v']['@value'] \
            if ('@context' in jsonldSchema and
                'v' in jsonldSchema['@context'] and
                '@value' in jsonldSchema['@context']['v']) \
            else 1
