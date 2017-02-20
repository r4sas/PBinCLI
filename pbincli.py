#! /usr/bin/env python2.7
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
    --comment "My file" --password mypass image.txt"""
    )
    send_parser.add_argument("-B", "--burn", default=False, action="store_true", help="burn sent paste after reading")
    send_parser.add_argument("-c", "--comment", help="comment in quotes")
    send_parser.add_argument("-D", "--discus", default=False, action="store_true", help="open discussion of sent paste")
    send_parser.add_argument("-E", "--expire", default="1day", action="store", help="expiration of paste (default: 1day)")
    send_parser.add_argument("-F", "--format", default="plaintext", action="store", choices=["plaintext", "syntaxhighlighting", "markdown"], help="format of paste (default: plaintext)")
    send_parser.add_argument("-p", "--password", help="password for crypting paste")
    send_parser.add_argument("-d", "--debug", default=False, action="store_true", help="enable debug")
    send_parser.add_argument("-f", "--file", help="example: image.jpg or full path to file")
    send_parser.set_defaults(func=pbincli.actions.send)

    get_parser = subparsers.add_parser("get", description="Get data from PrivateBin instance", usage="""
%(prog)s pasteid#password"""
    )
    get_parser.add_argument("pasteinfo", help="example: aabb#cccddd")
    get_parser.add_argument("-d", "--debug", default=False, action="store_true", help="enable debug")
    get_parser.set_defaults(func=pbincli.actions.get)

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
