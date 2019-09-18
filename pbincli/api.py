import requests
from requests import HTTPError
from pbincli.utils import PBinCLIError

class PrivateBin:
    def __init__(self, settings=None):
        self.server = settings['server']
        self.headers = {'X-Requested-With': 'JSONHttpRequest'}

        if settings['proxy']:
            self.proxy = {settings['proxy'].split('://')[0]: settings['proxy']}
        else:
            self.proxy = {}

        if settings['no_insecure_warning']:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.session = requests.Session()
        self.session.verify = not settings['no_check_certificate']

    def post(self, request):
        result = self.session.post(
            url = self.server,
            headers = self.headers,
            proxies = self.proxy,
            data = request)

        try:
            return result.json()
        except ValueError:
            PBinCLIError("Unable parse response as json. Received (size = {}):\n{}".format(len(result.text), result.text))


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
            PBinCLIError("Something went wrong...\nError:\t\t{}".format(result['message']))
        else:
            PBinCLIError("Something went wrong...\nError: Empty response.")


    def getVersion(self):
        jsonldSchema = self.session.get(
            url = self.server + '?jsonld=paste',
            proxies = self.proxy).json()
        return jsonldSchema['@context']['v']['@value'] \
            if ('@context' in jsonldSchema and
                'v' in jsonldSchema['@context'] and
                '@value' in jsonldSchema['@context']['v']) \
            else 1

class Shortener:
    """Some parts of this class was taken from
    python-yourls (https://github.com/tflink/python-yourls/) library
    """
    def __init__(self, settings=None):
        self.api = settings['short_api']

        # we checking which service is used, because some services doesn't require
        # any authentication, or have only one domain on which it working
        if self.api == 'yourls':
            if not settings['short_url']:
                PBinCLIError("YOURLS: An API URL is required")
            self.apiurl = settings['short_url']

            if settings['short_user'] and settings['short_pass'] and settings['short_token'] is None:
                self.auth_args = {'username': settings['short_user'], 'password': settings['short_pass']}
            elif settings['short_user'] is None and settings['short_pass'] is None and settings['short_token']:
                self.auth_args = {'signature': settings['short_token']}
            elif settings['short_user'] is None and settings['short_pass'] is None and settings['short_token'] is None:
                self.auth_args = {}
            else:
                PBinCLIError("YOURLS: either username and password or token are required. Otherwise set to default (None)")

        if settings['proxy']:
            self.proxy = {settings['proxy'].split('://')[0]: settings['proxy']}
        else:
            self.proxy = {}

        if settings['no_insecure_warning']:
            from requests.packages.urllib3.exceptions import InsecureRequestWarning
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

        self.session = requests.Session()
        self.session.verify = not settings['no_check_certificate']

    def getlink(self, url):
        if self.api == 'yourls':
            request = {'action': 'shorturl', 'format': 'json', 'url': url}
            request.update(self.auth_args)

            result = self.session.post(
                url = self.apiurl,
                proxies = self.proxy,
                data = request)

            try:
                result.raise_for_status()
            except HTTPError as http_exc:
                try:
                    response = result.json()
                except:
                    PBinCLIError("YOURLS: Unable parse response. Received (size = {}):\n{}".format(len(result.text), result.text))
                else:
                    PBinCLIError("YOURLS: Received error from API: {} with JSON {}".format(result, response))
            else:
                response = result.json()

                if {'status', 'code', 'message'} <= set(response.keys()):
                    status = response['status']
                    code = response['code']
                    message = response['message']

                    if status == 'fail':
                        PBinCLIError("YOURLS: Received error from API: {}".format(response['message']))
                    if not 'shorturl' in response:
                        PBinCLIError("YOURLS: Unknown error: {}".format(response['message']))
                    else:
                        print("Short Link:\t{}".format(response['shorturl']))
                else:
                    PBinCLIError("YOURLS: No status, code and message fields in response! Received:\n{}".format(response))

        elif self.api == 'clckru':
            # from urllib.parse import quote_plus
            request = {'url': url}

            result = self.session.post(
                url = "https://clck.ru/--",
                proxies = self.proxy,
                data = request)
            print("Short Link:\t{}".format(result.text))
