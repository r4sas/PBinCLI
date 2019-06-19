import requests

class PrivateBin:
    def __init__(self, server, proxy=None):
        self.server = server
        self.headers = {'X-Requested-With': 'JSONHttpRequest'}
        if proxy:
            self.proxy = {proxy.split('://')[0]: proxy}
        else:
            self.proxy = {}


    def post(self, request):
        result = requests.post(
            url = self.server,
            headers = self.headers,
            proxies = self.proxy,
            data = request)

        try:
            return result.json()
        except ValueError as e:
            print("ERROR: Unable parse response as json. Received (size = {}):\n".format(len(result.text), result.text))
            exit(1)


    def get(self, request):
        return requests.get(
            url = self.server + "?" + request,
            headers = self.headers,
            proxies = self.proxy).json()


    def delete(self, request):
        # using try as workaround for versions < 1.3 due to we cant detect
        # if server used version 1.2, where auto-deletion is added
        try:
            result = requests.post(
                url = self.server,
                headers = self.headers,
                proxies = self.proxy,
                data = request).json()
        except ValueError as e:
            # unable parse response as json because it can be empty (1.2), so simulate correct answer
            from json import loads as json_loads
            result = json_loads('{"status":0}')

        if not result['status']:
            print("Paste successfully deleted!")
        elif result['status']:
            print("Something went wrong...\nError:\t\t{}".format(result['message']))
            exit(1)
        else:
            print("Something went wrong...\nError: Empty response.")
            exit(1)


    def getVersion(self):
        jsonldSchema = requests.get(
            url = self.server + '?jsonld=paste',
            proxies = self.proxy).json()
        return jsonldSchema['@context']['v']['@value'] \
            if ('@context' in jsonldSchema and
                'v' in jsonldSchema['@context'] and
                '@value' in jsonldSchema['@context']['v']) \
            else 1
