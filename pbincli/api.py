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
        elif self.api == 'isgd' or self.api == 'vgd':
            if self.api == 'isgd':
                self.apiurl = 'https://is.gd/'
            else:
                self.apiurl = 'https://v.gd/'

            self.useragent = 'Mozilla/5.0 (compatible; pbincli - https://github.com/r4sas/pbincli/)'


        self.session, self.proxy = _config_requests(settings)

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

        elif self.api == 'clckru':
            request = {'url': url}

            try:
                result = self.session.post(
                    url = "https://clck.ru/--",
                    proxies = self.proxy,
                    data = request)
                print("Short Link:\t{}".format(result.text))
            except Exception as ex:
                PBinCLIError("clck.ru: unexcepted behavior: {}".format(ex))

        elif self.api == 'tinyurl':
            request = {'url': url}

            try:
                result = self.session.post(
                    url = "https://tinyurl.com/api-create.php",
                    proxies = self.proxy,
                    data = request)
                print("Short Link:\t{}".format(result.text))
            except Exception as ex:
                PBinCLIError("TinyURL: unexcepted behavior: {}".format(ex))

        elif self.api == 'isgd' or self.api == 'vgd':
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

        elif self.api == 'cuttly':
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

        '''
        # That code needs testing. API requires username and apiKey or accessToken to work.
        elif self.api == 'bitly':
            request = {'url': url}
            headers = {'X-Requested-With': 'XMLHttpRequest'}

            try:
                result = self.session.post(
                    url = "https://bitly.com/",
                    headers = headers,
                    proxies = self.proxy,
                    data = request)
                response = result.json()
                if response['data'] and response['status_code'] == 200:
                    print("Short Link:\t{}".format(response['data']['anon_shorten']['link']))
                elif response['status_txt']:
                    errcode = response['status_txt'] or 'DEFAULT'
                    friendlyError = {
                        'RATE_LIMIT_EXCEEDED': 'Whoa - you\'ve exceeded your quota. Create a free account to keep shortening.',
                        'INVALID_ARG_URL': 'Unable to shorten that link. It is not a valid url.',
                        'INVALID_ARG_LONGURL': 'Unable to shorten that link. It is not a valid url.',
                        'ALREADY_A_BITLY_LINK': 'That is already a Bitly link',
                        'UNKNOWN_ERROR': 'Woops. Something went wrong. Please try again.',
                        'DEFAULT': 'An error occurred'
                    }
                    PBinCLIError("bitly: got error from API: {}".format(friendlyError[errcode]))
            except Exception as ex:
                PBinCLIError("bitly: unexcepted behavior: {}".format(ex))
        '''
