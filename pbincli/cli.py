#!/usr/bin/env python
import os, sys, argparse

import pbincli.actions
from pbincli.api import PrivateBin
from pbincli.utils import PBinCLIException, validate_url

CONFIG_PATHS = [os.path.join(".", "pbincli.conf", ),
       os.path.join(os.getenv("HOME") or "~", ".config", "pbincli", "pbincli.conf") ]

def read_config(filename):
    """Read config variables from a file"""
    settings = {}
    with open(filename) as f:
        for l in f.readlines():
            key, value = l.strip().split("=")
            settings[key.strip()] = value.strip()

    return settings

def main():
    parser = argparse.ArgumentParser()
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
    # URL shortener
    send_parser.add_argument("-S", "--short", default=False, action="store_true", help="use URL shortener")
    send_parser.add_argument("--short-api", default=argparse.SUPPRESS, action="store", choices=["tinyurl", "clckru", "isgd", "vgd", "cuttly", "yourls"], help="API used by shortener service")
    send_parser.add_argument("--short-url", default=argparse.SUPPRESS, help="URL of shortener service API")
    send_parser.add_argument("--short-user", default=argparse.SUPPRESS, help="Shortener username")
    send_parser.add_argument("--short-pass", default=argparse.SUPPRESS, help="Shortener password")
    send_parser.add_argument("--short-token", default=argparse.SUPPRESS, help="Shortener token")
    # Connection options
    send_parser.add_argument("-s", "--server", default=argparse.SUPPRESS, help="PrivateBin service URL (default: https://paste.i2pd.xyz/)")
    send_parser.add_argument("-x", "--proxy", default=argparse.SUPPRESS, help="Proxy server address (default: None)")
    send_parser.add_argument("--no-check-certificate", default=False, action="store_true", help="disable certificate validation")
    send_parser.add_argument("--no-insecure-warning", default=False, action="store_true", help="suppress InsecureRequestWarning (only with --no-check-certificate)")
    #
    send_parser.add_argument("-d", "--debug", default=False, action="store_true", help="enable debug")
    send_parser.add_argument("--dry", default=False, action="store_true", help="invoke dry run")
    send_parser.add_argument("stdin", help="input paste text from stdin", nargs="?", type=argparse.FileType("r"), default=sys.stdin)
    send_parser.set_defaults(func=pbincli.actions.send)

    # a get command
    get_parser = subparsers.add_parser("get", description="Get data from PrivateBin instance")
    get_parser.add_argument("pasteinfo", help="example: aabb#cccddd")
    get_parser.add_argument("-p", "--password", help="password for decrypting paste")
    get_parser.add_argument("--no-check-certificate", default=False, action="store_true", help="disable certificate validation")
    get_parser.add_argument("--no-insecure-warning", default=False, action="store_true", help="suppress InsecureRequestWarning (only with --no-check-certificate)")
    get_parser.add_argument("-d", "--debug", default=False, action="store_true", help="enable debug")
    get_parser.set_defaults(func=pbincli.actions.get)

    # a delete command
    delete_parser = subparsers.add_parser("delete", description="Delete paste from PrivateBin instance using token")
    delete_parser.add_argument("-p", "--paste", required=True, help="paste id")
    delete_parser.add_argument("-t", "--token", required=True, help="paste deletion token")
    delete_parser.add_argument("--no-check-certificate", default=False, action="store_true", help="disable certificate validation")
    delete_parser.add_argument("--no-insecure-warning", default=False, action="store_true", help="suppress InsecureRequestWarning (only with --no-check-certificate)")
    delete_parser.add_argument("-d", "--debug", default=False, action="store_true", help="enable debug")
    delete_parser.set_defaults(func=pbincli.actions.delete)

    # parse arguments
    args = parser.parse_args()

    CONFIG = {
        'server': 'https://paste.i2pd.xyz/',
        'proxy': None,
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
    CONFIG['server'] = validate_url(CONFIG['server'])

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
