import requests

class PrivateBin:
    def __init__(self, server, settings=None):
        self.server = server
        self.headers = {'X-Requested-With': 'JSONHttpRequest'}

        if settings['proxy']:
            self.proxy = {settings['proxy'].split('://')[0]: settings['proxy']}
        else:
            self.proxy = {}

        if settings['noinsecurewarn']:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.session = requests.Session()
        self.session.verify = settings['nocheckcert']

    def post(self, request):
        result = self.session.post(
            url = self.server,
            headers = self.headers,
            proxies = self.proxy,
            data = request)

        try:
            return result.json()
        except ValueError:
            print("ERROR: Unable parse response as json. Received (size = {}):\n{}".format(len(result.text), result.text))
            exit(1)


    def get(self, request):
        return self.session.get(
            url = self.server + "?" + request,
            headers = self.headers,
            proxies = self.proxy).json()


    def delete(self, request):
        # using try as workaround for versions < 1.3 due to we cant detect
        # if server used version 1.2, where auto-deletion is added
        try:
            result = self.session.post(
                url = self.server,
                headers = self.headers,
                proxies = self.proxy,
                data = request).json()
        except ValueError:
            # unable parse response as json because it can be empty (1.2), so simulate correct answer
            print("NOTICE: Received empty response. We interpret that as our paste has already been deleted.")
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
        jsonldSchema = self.session.get(
            url = self.server + '?jsonld=paste',
            proxies = self.proxy).json()
        return jsonldSchema['@context']['v']['@value'] \
            if ('@context' in jsonldSchema and
                'v' in jsonldSchema['@context'] and
                '@value' in jsonldSchema['@context']['v']) \
            else 1
