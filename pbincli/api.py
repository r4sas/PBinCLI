import requests
from requests import HTTPError
from pbincli.utils import PBinCLIError

def _config_requests(settings=None):
    if settings['proxy']:
        proxy = {settings['proxy'].split('://')[0]: settings['proxy']}
    else:
        proxy = {}

    if settings['no_insecure_warning']:
        from requests.packages.urllib3.exceptions import InsecureRequestWarning
        requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

    session = requests.Session()
    session.verify = not settings['no_check_certificate']

    return session, proxy


class PrivateBin:
    def __init__(self, settings=None):
        self.server = settings['server']
        self.headers = {'X-Requested-With': 'JSONHttpRequest'}

        self.session, self.proxy = _config_requests(settings)

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
            self._yourls_init(settings)
        elif self.api == 'isgd' or self.api == 'vgd':
            self._gd_init()

        self.session, self.proxy = _config_requests(settings)


    def _yourls_init(self, settings):
        if not settings['short_url']:
            PBinCLIError("YOURLS: An API URL is required")

        # setting API URL
        apiurl = settings['short_url']
        if apiurl.endswith('/yourls-api.php'):
            self.apiurl = apiurl
        elif apiurl.endswith('/'):
            self.apiurl = apiurl + 'yourls-api.php'
        else:
            PBinCLIError("YOURLS: Incorrect URL is provided.\n" +
                "It must contain full address to 'yourls-api.php' script (like https://example.com/yourls-api.php)\n" +
                "or just contain instance URL with '/' at the end (like https://example.com/)")

        # validating for required credentials
        if settings['short_user'] and settings['short_pass'] and settings['short_token'] is None:
            self.auth_args = {'username': settings['short_user'], 'password': settings['short_pass']}
        elif settings['short_user'] is None and settings['short_pass'] is None and settings['short_token']:
            self.auth_args = {'signature': settings['short_token']}
        elif settings['short_user'] is None and settings['short_pass'] is None and settings['short_token'] is None:
            self.auth_args = {}
        else:
            PBinCLIError("YOURLS: either username and password or token are required. Otherwise set to default (None)")


    def _gd_init(self):
        if self.api == 'isgd':
            self.apiurl = 'https://is.gd/'
        else:
            self.apiurl = 'https://v.gd/'
        self.useragent = 'Mozilla/5.0 (compatible; pbincli - https://github.com/r4sas/pbincli/)'


    def getlink(self, url):
        # that is api -> function mapper for running service-related function when getlink() used
        servicesList = {
            'yourls': self._yourls,
            'clckru': self._clckru,
            'tinyurl': self._tinyurl,
            'isgd': self._gd,
            'vgd': self._gd,
            'cuttly': self._cuttly
        }
        # run function selected by choosen API
        servicesList[self.api](url)


    def _yourls(self,url):
        request = {'action': 'shorturl', 'format': 'json', 'url': url}
        request.update(self.auth_args)

        result = self.session.post(
            url = self.apiurl,
            proxies = self.proxy,
            data = request)

        try:
            result.raise_for_status()
        except HTTPError:
            try:
                response = result.json()
            except ValueError:
                PBinCLIError("YOURLS: Unable parse response. Received (size = {}):\n{}".format(len(result.text), result.text))
            else:
                PBinCLIError("YOURLS: Received error from API: {} with JSON {}".format(result, response))
        else:
            response = result.json()

            if {'status', 'statusCode', 'message'} <= set(response.keys()):
                if response['status'] == 'fail':
                    PBinCLIError("YOURLS: Received error from API: {}".format(response['message']))
                if not 'shorturl' in response:
                    PBinCLIError("YOURLS: Unknown error: {}".format(response['message']))
                else:
                    print("Short Link:\t{}".format(response['shorturl']))
            else:
                PBinCLIError("YOURLS: No status, statusCode or message fields in response! Received:\n{}".format(response))


    def _clckru(self, url):
        request = {'url': url}

        try:
            result = self.session.post(
                url = "https://clck.ru/--",
                proxies = self.proxy,
                data = request)
            print("Short Link:\t{}".format(result.text))
        except Exception as ex:
            PBinCLIError("clck.ru: unexcepted behavior: {}".format(ex))


    def _tinyurl(self, url):
        request = {'url': url}

        try:
            result = self.session.post(
                url = "https://tinyurl.com/api-create.php",
                proxies = self.proxy,
                data = request)
            print("Short Link:\t{}".format(result.text))
        except Exception as ex:
            PBinCLIError("TinyURL: unexcepted behavior: {}".format(ex))


    def _gd(self, url):
        request = {
            'format': 'json',
            'url': url,
            'logstats': 0 # we don't want use any statistics
        }
        headers = { 'User-Agent': self.useragent}

        try:
            result = self.session.post(
                url = self.apiurl + "create.php",
                headers = headers,
                proxies = self.proxy,
                data = request)

            response = result.json()

            if 'shorturl' in response:
                print("Short Link:\t{}".format(response['shorturl']))
            else:
                PBinCLIError("{}: got error {} from API: {}".format(
                    "is.gd" if self.api == 'isgd' else 'v.gd',
                    response['errorcode'],
                    response['errormessage']))

        except Exception as ex:
            PBinCLIError("{}: unexcepted behavior: {}".format(
                "is.gd" if self.api == 'isgd' else 'v.gd',
                ex))


    def _cuttly(self, url):
        request = {
            'url': url,
            'domain': 0
        }

        try:
            result = self.session.post(
                url = "https://cutt.ly/scripts/shortenUrl.php",
                proxies = self.proxy,
                data = request)
            print("Short Link:\t{}".format(result.text))
        except Exception as ex:
            PBinCLIError("cutt.ly: unexcepted behavior: {}".format(ex))
