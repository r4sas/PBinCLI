"""Action functions for argparser"""
import base64
import pbincli.actions
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes
from pbincli.sjcl_gcm import SJCL
from pbincli.transports import privatebin
from pbincli.utils import PBinCLIException, check_readable, check_writable
from zlib import compress

def send(args):
    """ Sub-command for sending paste """
    check_readable(args.filename)
    with open(args.filename, "rb") as f:
        contents = f.read()
    file = base64.b64encode(compress(contents))

    passphrase =  base64.b64encode(get_random_bytes(32))
    if not args.password:
        password = passphrase
    else:
        p = SHA256.new()
        p.update(args.password.encode("UTF-8"))
        password = passphrase + p.hexdigest().encode("UTF-8")

    data = SJCL().encrypt(file, password)
    request = "data={}&expire={}&formatter={}&burnafterreading={}&opendiscussion={}".format(data, args.expire, args.format, int(args.burn), int(args.discus))
    '''Here we must run function post from pbincli.transports'''
    print(request)
    privatebin().post(request)
