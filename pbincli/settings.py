def init():
    global server, proxies, useproxy

    """Edit that variables"""
    server = "https://privatebin.net/"
    proxies = {'http': 'http://127.0.0.1:4444'}
    useproxy = False

    """ There is nothing more to do :D """

    """if you set useproxy to false, we clean proxies variable"""
    if useproxy == False:
        proxies = {}
