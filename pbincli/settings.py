def init():
    global server, proxies, useproxy

    """ Edit that variables """
    server = "http://paste.r4sas.i2p/"
    proxies = {'http': 'http://127.0.0.1:4444'}

    """ True/False """
    useproxy = True

    """ There is nothing more to do :D """

    """if you set useproxy to false, we clean proxies variable"""
    if useproxy == False:
        proxies = {}
