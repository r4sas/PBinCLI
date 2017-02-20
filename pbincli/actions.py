"""Action functions for argparser"""
import json
import os
import pbincli.actions
'''from pbincli.sjcl_gcm import SJCL'''
import pbincli.sjcl_simple
import pbincli.utils
from base64 import b64encode
from Crypto.Hash import SHA256
from pbincli.transports import privatebin
from zlib import compress


def send(args):
    """ Sub-command for sending paste """
    #check_readable(args.filename)
    #with open(args.filename, "rb") as f:
    #    contents = f.read()
    #file = b64encode(compress(contents))
    data = b'Test!'


    passphrase = os.urandom(32)
    if args.debug: print("Passphrase: {}".format(passphrase))
    if args.password:
        p = SHA256.new()
        p.update(args.password.encode("UTF-8"))
        passphrase = b64encode(passphrase + p.hexdigest().encode("UTF-8"))

    else:
        passphrase = b64encode(passphrase)
    if args.degub: print("Password:\t{}".format(passphrase))


    #data = SJCL().encrypt(file, password.decode("UTF-8"))
    #cipher = pbincli.sjcl_simple.encrypt(b64encode(passphrase), file)
    """Sending text from 'data' string"""
    cipher = pbincli.sjcl_simple.encrypt(passphrase, data)
    request = {'data':json.dumps(cipher, ensure_ascii=False).replace(' ',''),'expire':args.expire,'formatter':args.format,'burnafterreading':int(args.burn),'opendiscussion':int(args.discus)
    }
    if args.debug: print("Request:\t{}".format(request))


    result, server = privatebin().post(request)
    if args.debug: print("Response:\t{}\n".format(result.decode("UTF-8")))
    result = json.loads(result)
    """Standart response: {"status":0,"id":"aaabbb","url":"\/?aaabbb","deletetoken":"aaabbbccc"}"""
    if result['status'] == 0:
        print("Paste uploaded!\nPasteID:\t{}\nPassword:\t{}\nDelete token:\t{}\n\nLink:\t{}?{}#{}".format(result['id'], passphrase.decode("UTF-8"), result['deletetoken'], server, result['id'], passphrase.decode("UTF-8")))

    else:
        print("Something went wrong...\nError:\t{}".format(result['error']))
        sys.exit(1)


def get(args):
    paste = args.pasteinfo.split("#")
    if paste[0] and paste[1]:
        if args.debug: print("PasteID:\t{}\nPassword:\t{}\n".format(paste[0], paste[1]))
        result = privatebin().get(args.pasteinfo)
    else:
        print("PBinCLI error: Incorrect request")
        sys.exit(1)


    if args.debug: print("Response:\t{}\n".format(result.decode("UTF-8")))
    result = json.loads(result)
    if result['status'] == 0:
        print("Paste received!\n")
        text = pbincli.utils.json_loads_byteified(result['data'])
        out =  pbincli.sjcl_simple.decrypt(paste[1], text)
        print(out)

        if 'burnafterreading' in result['meta'] and result['meta']['burnafterreading']:
            print("Meow!")

    else:
        print("Something went wrong...\nError:\t{}".format(result['error']))
        sys.exit(1)
