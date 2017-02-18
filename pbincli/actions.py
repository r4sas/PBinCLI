"""Action functions for argparser"""
import pbincli.sjcl_gcm
import pbincli.actions
from pbincli.utils import PBinCLIException, check_readable, check_writable

def send(args):
    print("Meow!")
