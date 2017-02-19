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
    send_parser = subparsers.add_parser("send", description="Send data to PrivateBin instance", usage="""
%(prog)s --burn --discus --expire 1day --format plaintext \\
    --password mypass image.txt"""
    )
    send_parser.add_argument("-b", "--burn", default=False, action="store_true", help="burn sent paste after reading")
    send_parser.add_argument("-d", "--discus", default=False, action="store_true", help="open discussion of sent paste")
    send_parser.add_argument("-e", "--expire", default="1day", action="store", help="expiration of paste (default: 1day)")
    send_parser.add_argument("-f", "--format", default="plaintext", action="store", help="format of paste (default: plaintext)")
    send_parser.add_argument("-p", "--password", help="password for crypting paste")
    send_parser.add_argument("filename", help="filename (example: image.jpg)")
    send_parser.set_defaults(func=pbincli.actions.send)

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
