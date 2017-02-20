"""Action functions for argparser"""
import json
#import mimetypes
import os
import pbincli.actions
import sys
#import pbincli.sjcl_gcm
import pbincli.sjcl_simple
import pbincli.utils
from base64 import b64encode, b64decode
from Crypto.Hash import SHA256
from pbincli.transports import privatebin
from zlib import compress, decompress


def send(args):
    if args.comment:
        text = args.comment
    else:
        text = "Test!"

    #check_readable(args.filename)
    #with open(args.filename, "rb") as f:
    #    contents = f.read()
    #file = b64encode(compress(contents))

    passphrase = os.urandom(32)
    if args.debug: print("Passphrase: {}".format(passphrase))
    if args.password:
        p = SHA256.new()
        p.update(args.password.encode("UTF-8"))
        passphrase = b64encode(passphrase + p.hexdigest().encode("UTF-8"))
    else:
        passphrase = b64encode(passphrase)
    if args.debug: print("Password:\t{}".format(passphrase))

    """Sending text from 'data' string"""
    #cipher = SJCL().encrypt(b64encode(text), passphrase)
    cipher = pbincli.sjcl_simple.encrypt(passphrase, text)
    request = {'data':json.dumps(cipher, ensure_ascii=False).replace(' ',''),'expire':args.expire,'formatter':args.format,'burnafterreading':int(args.burn),'opendiscussion':int(args.discus)}
    if args.debug: print("Request:\t{}".format(request))

    result, server = privatebin().post(request)
    if args.debug: print("Response:\t{}\n".format(result.decode("UTF-8")))
    result = json.loads(result)
    """Standart response: {"status":0,"id":"aaabbb","url":"\/?aaabbb","deletetoken":"aaabbbccc"}"""
    if result['status'] == 0:
        print("Paste uploaded!\nPasteID:\t{}\nPassword:\t{}\nDelete token:\t{}\n\nLink:\t{}?{}#{}".format(result['id'], passphrase.decode("UTF-8"), result['deletetoken'], server, result['id'], passphrase.decode("UTF-8")))
    else:
        print("Something went wrong...\nError:\t{}".format(result['message']))
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
        out = pbincli.sjcl_simple.decrypt(paste[1], text)
        #out = pbincli.sjcl_gcm.SJCL().decrypt(text, paste[1])
        print(out)

        if 'burnafterreading' in result['meta'] and result['meta']['burnafterreading']:
            result = privatebin().delete(paste[0], 'burnafterreading')
            if args.debug: print("Delete response:\t{}\n".format(result.decode("UTF-8")))
    else:
        print("Something went wrong...\nError:\t{}".format(result['message']))
        sys.exit(1)
