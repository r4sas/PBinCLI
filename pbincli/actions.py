"""Action functions for argparser"""
import json
import os
import pbincli.actions
'''from pbincli.sjcl_gcm import SJCL'''
import pbincli.sjcl_simple
from base64 import b64encode
from Crypto.Hash import SHA256
from pbincli.transports import privatebin
from pbincli.utils import PBinCLIException, check_readable, check_writable
from zlib import compress

def send(args):
    """ Sub-command for sending paste """
    #check_readable(args.filename)
    #with open(args.filename, "rb") as f:
    #    contents = f.read()
    #file = b64encode(compress(contents))

    data = b'Test!'

    passphrase = os.urandom(32)
    #print("Passphrase: {}".format(passphrase))
    if args.password:
        #print("Password: {}".format(password))
        p = SHA256.new()
        p.update(args.password.encode("UTF-8"))
        passphrase = passphrase + p.hexdigest().encode("UTF-8")


    #data = SJCL().encrypt(file, password.decode("UTF-8"))
    """Sending text from 'data' string"""
    #cipher = pbincli.sjcl_simple.encrypt(b64encode(passphrase), file)
    cipher = pbincli.sjcl_simple.encrypt(b64encode(passphrase), data)
    request = {'data':json.dumps(cipher, ensure_ascii=False),'expire':args.expire,'formatter':args.format,'burnafterreading':int(args.burn),'opendiscussion':int(args.discus)
    }
    print(request)
    '''Here we run function post from pbincli.transports'''
    privatebin().post(request, b64encode(passphrase))
