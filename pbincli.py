#! /usr/bin/env python3
import os
import sys
import argparse

import pbincli.actions
from pbincli.utils import PBinCLIException

def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(title="actions", help="List of commands")
    # a send command
    send_parser = subparsers.add_parser("send", description="Send data to PrivateBin instance", usage="""%(prog)s --cert data/user_at_mail.i2p.crt --private-key data/priv_key.pem --signer-id user@mail.i2p""")
    send_parser.add_argument("-b", "--burn", default=False, action="store_true", help="Burn after reading")
    send_parser.add_argument("-d", "--discus", default=False, action="store_true", help="Open discussion")
    send_parser.add_argument("-e", "--expire", default="1day", action="store", help="Expiration of paste")
    send_parser.add_argument("-f", "--format", default="plaintext", action="store", help="Format of text paste")
    send_parser.add_argument("-p", "--password", default=None, help="RSA private key (default: data/priv_key.pem)")
    send_parser.add_argument("filename", type=argparse.FileType('r'), help="Filename (example: image.jpg)")
    send_parser.set_defaults(func=pbincli.actions.send)
    '''# a get command
    get_parser = subparsers.add_parser("get", description="Recieve data from PrivateBin instance", usage="""echo $YOUR_PASSWORD | %(prog)s --netdb /path/to/netDb --private-key data/priv_key.pem --outfile output/i2pseeds.su3 --signer-id user@mail.i2p""")
    get_parser.add_argument("--signer-id", required=True, help="Identifier of certificate (example: user@mail.i2p)")
    get_parser.add_argument("--private-key", default="data/priv_key.pem", help="RSA private key (default: data/priv_key.pem)")
    get_parser.add_argument("-o", "--outfile", default="output/i2pseeds.su3", help="Output file (default: output/i2pseeds.su3)")
    get_parser.add_argument("--netdb", required=True, help="Path to netDb folder (example: ~/.i2pd/netDb)")
    get_parser.set_defaults(func=pyseeder.actions.reseed)'''
    # parse arguments
    args = parser.parse_args()
    if hasattr(args, "func"):
        try:
            args.func(args)
        except PBinCLIException as pe:
            print("PBinCLI error: {}".format(pe))
            sys.exit(1)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
