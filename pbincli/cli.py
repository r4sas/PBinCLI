#!/usr/bin/env python
import os, sys, argparse

import pbincli.actions
from pbincli.api import PrivateBin
from pbincli.utils import PBinCLIException, PBinCLIError, validate_url_ending

CONFIG_PATHS = [
    os.path.join(".", "pbincli.conf", ),
    os.path.join(os.getenv("HOME") or "~", ".config", "pbincli", "pbincli.conf")
]

if sys.platform == "win32":
    CONFIG_PATHS.append(os.path.join(os.getenv("APPDATA"), "pbincli", "pbincli.conf"))
elif sys.platform == "darwin":
    CONFIG_PATHS.append(os.path.join(os.getenv("HOME") or "~", "Library", "Application Support", "pbincli", "pbincli.conf"))

def read_config(filename):
    """Read config variables from a file"""
    settings = {}
    with open(filename) as f:
        for l in f.readlines():
            if len(l.strip()) == 0:
                continue
            try:
                key, value = l.strip().split("=", 1)
                settings[key.strip()] = value.strip()
            except ValueError:
                PBinCLIError("Unable to parse config file, please check it for errors.")

    return settings

def main():
    parser = argparse.ArgumentParser(description='Full-featured PrivateBin command-line client')
    subparsers = parser.add_subparsers(title="actions", help="List of commands")

    # a send command
    send_parser = subparsers.add_parser("send", description="Send data to PrivateBin instance")
    send_parser.add_argument("-t", "--text", help="text in quotes. Ignored if used stdin. If not used, forcefully used stdin")
    send_parser.add_argument("-f", "--file", help="example: image.jpg or full path to file")
    send_parser.add_argument("-p", "--password", help="password for encrypting paste")
    send_parser.add_argument("-E", "--expire", default="1day", action="store",
        choices=["5min", "10min", "1hour", "1day", "1week", "1month", "1year", "never"], help="paste lifetime (default: 1day)")
    send_parser.add_argument("-B", "--burn", default=False, action="store_true", help="burn sent paste after reading")
    send_parser.add_argument("-D", "--discus", default=False, action="store_true", help="open discussion for sent paste")
    send_parser.add_argument("-F", "--format", default="plaintext", action="store",
        choices=["plaintext", "syntaxhighlighting", "markdown"], help="format of text (default: plaintext)")
    send_parser.add_argument("-q", "--notext", default=False, action="store_true", help="don't send text in paste")
    send_parser.add_argument("-c", "--compression", default="zlib", action="store",
        choices=["zlib", "none"], help="set compression for paste (default: zlib). Note: works only on v2 paste format")
    ## URL shortener
    send_parser.add_argument("-S", "--short", default=False, action="store_true", help="use URL shortener")
    send_parser.add_argument("--short-api", default=argparse.SUPPRESS, action="store",
        choices=["tinyurl", "clckru", "isgd", "vgd", "cuttly", "yourls", "custom"], help="API used by shortener service")
    send_parser.add_argument("--short-url", default=argparse.SUPPRESS, help="URL of shortener service API")
    send_parser.add_argument("--short-user", default=argparse.SUPPRESS, help="Shortener username")
    send_parser.add_argument("--short-pass", default=argparse.SUPPRESS, help="Shortener password")
    send_parser.add_argument("--short-token", default=argparse.SUPPRESS, help="Shortener token")
    ## Connection options
    send_parser.add_argument("-s", "--server", default=argparse.SUPPRESS, help="Instance URL (default: https://paste.i2pd.xyz/)")
    send_parser.add_argument("-x", "--proxy", default=argparse.SUPPRESS, help="Proxy server address (default: None)")
    send_parser.add_argument("--no-check-certificate", default=False, action="store_true", help="disable certificate validation")
    send_parser.add_argument("--no-insecure-warning", default=False, action="store_true",
        help="suppress InsecureRequestWarning (only with --no-check-certificate)")
    ##
    send_parser.add_argument("-L", "--mirrors", default=argparse.SUPPRESS, help="Comma-separated list of mirrors of service with scheme (default: None)")
    send_parser.add_argument("-v", "--verbose", default=False, action="store_true", help="enable verbose output")
    send_parser.add_argument("-d", "--debug", default=False, action="store_true", help="enable debug output")
    send_parser.add_argument("--dry", default=False, action="store_true", help="invoke dry run")
    send_parser.add_argument("stdin", help="input paste text from stdin", nargs="?", type=argparse.FileType("r"), default=sys.stdin)
    send_parser.set_defaults(func=pbincli.actions.send)

    # a get command
    get_parser = subparsers.add_parser("get", description="Get data from PrivateBin instance")
    get_parser.add_argument("pasteinfo", help="\"PasteID#Passphrase\" or full URL")
    get_parser.add_argument("-p", "--password", help="password for decrypting paste")
    ## Connection options
    get_parser.add_argument("-s", "--server", default=argparse.SUPPRESS, help="Instance URL (default: https://paste.i2pd.xyz/, ignored if URL used in pasteinfo)")
    get_parser.add_argument("-x", "--proxy", default=argparse.SUPPRESS, help="Proxy server address (default: None)")
    get_parser.add_argument("--no-check-certificate", default=False, action="store_true", help="disable certificate validation")
    get_parser.add_argument("--no-insecure-warning", default=False, action="store_true",
        help="suppress InsecureRequestWarning (only with --no-check-certificate)")
    ##
    get_parser.add_argument("-v", "--verbose", default=False, action="store_true", help="enable verbose output")
    get_parser.add_argument("-d", "--debug", default=False, action="store_true", help="enable debug output")
    get_parser.set_defaults(func=pbincli.actions.get)

    # a delete command
    delete_parser = subparsers.add_parser("delete", description="Delete paste from PrivateBin instance using token")
    delete_parser.add_argument("-p", "--paste", required=True, help="paste id")
    delete_parser.add_argument("-t", "--token", required=True, help="paste deletion token")
    ## Connection options
    delete_parser.add_argument("-s", "--server", default=argparse.SUPPRESS, help="Instance URL (default: https://paste.i2pd.xyz/)")
    delete_parser.add_argument("-x", "--proxy", default=argparse.SUPPRESS, help="Proxy server address (default: None)")
    delete_parser.add_argument("--no-check-certificate", default=False, action="store_true", help="disable certificate validation")
    delete_parser.add_argument("--no-insecure-warning", default=False, action="store_true",
        help="suppress InsecureRequestWarning (only with --no-check-certificate)")
    ##
    delete_parser.add_argument("-v", "--verbose", default=False, action="store_true", help="enable verbose output")
    delete_parser.add_argument("-d", "--debug", default=False, action="store_true", help="enable debug output")
    delete_parser.set_defaults(func=pbincli.actions.delete)

    # parse arguments
    args = parser.parse_args()

    CONFIG = {
        'server': 'https://paste.i2pd.xyz/',
        'mirrors': None, # real example for paste.i2pd.xyz: 'http://privatebin.ygg/,http://privatebin.i2p/'
        'proxy': None,
        'short': False,
        'short_api': None,
        'short_url': None,
        'short_user': None,
        'short_pass': None,
        'short_token': None,
        'no_check_certificate': False,
        'no_insecure_warning': False
    }

    # Configuration preference order:
    # 1. Command line switches
    # 2. Environment variables
    # 3. Configuration file
    # 4. Default values below

    for p in CONFIG_PATHS:
        if os.path.exists(p):
            CONFIG.update(read_config(p))
            break

    for key in CONFIG.keys():
        var = "PRIVATEBIN_{}".format(key.upper())
        if var in os.environ: CONFIG[key] = os.getenv(var)
        # values from command line switches are preferred
        args_var = vars(args)
        if key in args_var:
            CONFIG[key] = args_var[key]

    # Re-validate PrivateBin instance URL
    CONFIG['server'] = validate_url_ending(CONFIG['server'])

    api_client = PrivateBin(CONFIG)

    if hasattr(args, "func"):
        try:
            args.func(args, api_client, settings=CONFIG)
        except PBinCLIException as pe:
            raise PBinCLIException("error: {}".format(pe))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
