"""Action functions for argparser"""
import json, os, ntpath, sys
import pbincli.actions, pbincli.sjcl_simple
from base64 import b64encode, b64decode
from Crypto.Hash import SHA256
from mimetypes import guess_type
from pbincli.transports import privatebin
from pbincli.utils import PBinCLIException, check_readable, check_writable, json_load_byteified
from zlib import compress, decompress


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def send(args):
    if args.comment:
        text = args.comment
    elif args.file:
        text = "Sending file to you!"
    else:
        print("Nothing to send!")
        sys.exit(1)

    passphrase = b64encode(os.urandom(32))
    if args.debug: print("Passphrase:\t{}".format(b64encode(passphrase)))
    if args.password:
        p = SHA256.new()
        p.update(args.password.encode("UTF-8"))
        password = passphrase + p.hexdigest().encode("UTF-8")
    else:
        password = passphrase
    if args.debug: print("Password:\t{}".format(password))

    if args.file:
        check_readable(args.file)
        with open(args.file, "rb") as f:
            contents = f.read()
            f.close()
        mime = guess_type(args.file)
        if args.debug: print("Filename:\t{}\nMIME-type:\t{}".format(path_leaf(args.file), mime[0]))

        file = "data:" + mime[0] + ";base64," + b64encode(contents)
        filename = path_leaf(args.file)

        cipherfile = pbincli.sjcl_simple.encrypt(password, file)
        cipherfilename = pbincli.sjcl_simple.encrypt(password, filename)

    """Sending text from 'data' string"""
    cipher = pbincli.sjcl_simple.encrypt(password, text)
    request = {'data':json.dumps(cipher, ensure_ascii=False).replace(' ',''),'expire':args.expire,'formatter':args.format,'burnafterreading':int(args.burn),'opendiscussion':int(args.discus)}
    if cipherfile and cipherfilename:
        request['attachment'] = json.dumps(cipherfile, ensure_ascii=False).replace(' ','')
        request['attachmentname'] = json.dumps(cipherfilename, ensure_ascii=False).replace(' ','')

    if args.debug: print("Request:\t{}".format(request))

    result, server = privatebin().post(request)
    if args.debug: print("Response:\t{}\n".format(result.decode("UTF-8")))
    result = json.loads(result)
    """Standart response: {"status":0,"id":"aaabbb","url":"\/?aaabbb","deletetoken":"aaabbbccc"}"""
    if result['status'] == 0:
        print("Paste uploaded!\nPasteID:\t{}\nPassword:\t{}\nDelete token:\t{}\n\nLink:\t{}?{}#{}".format(result['id'], passphrase, result['deletetoken'], server, result['id'], passphrase))
    else:
        print("Something went wrong...\nError:\t{}".format(result['message']))
        sys.exit(1)


def get(args):
    paste = args.pasteinfo.split("#")
    if paste[0] and paste[1]:
        if args.debug: print("PasteID:\t{}\nPassphrase:\t{}".format(paste[0], paste[1]))

        if args.password:
            p = SHA256.new()
            p.update(args.password.encode("UTF-8"))
            passphrase = paste[1] + p.hexdigest().encode("UTF-8")
        else:
            passphrase = paste[1]
        if args.debug: print("Password:\t{}".format(passphrase))

        result = privatebin().get(paste[0])

    else:
        print("PBinCLI error: Incorrect request")
        sys.exit(1)
    if args.debug: print("Response:\t{}\n".format(result.decode("UTF-8")))

    result = json.loads(result)
    if result['status'] == 0:
        print("Paste received! Text inside:")
        data = pbincli.utils.json_loads_byteified(result['data'])
        if args.debug: print("Text:\t{}".format(data))
        text = pbincli.sjcl_simple.decrypt(passphrase, data)
        print(text)

        check_writable("paste.txt")
        with open("paste.txt", "wb") as f:
            f.write(text)
            f.close

        if 'attachment' in result and 'attachmentname' in result:
            print("Found file, attached to paste. Decoding it and saving")
            cipherfile = pbincli.utils.json_loads_byteified(result['attachment']) 
            cipherfilename = pbincli.utils.json_loads_byteified(result['attachmentname'])
            if args.debug: print("Name:\t{}\nData:\t{}".format(cipherfilename, cipherfile))
            attachmentf = pbincli.sjcl_simple.decrypt(passphrase, cipherfile)
            attachmentname = pbincli.sjcl_simple.decrypt(passphrase, cipherfilename)

            attachment = str(attachmentf.split(',', 1)[1:])
            file = b64decode(attachment)
            filename = attachmentname
            if args.debug: print("Filename:\t{}\n".format(filename))

            check_writable(filename)
            with open(filename, "wb") as f:
                f.write(file)
                f.close

        if 'burnafterreading' in result['meta'] and result['meta']['burnafterreading']:
            print("Burn afrer reading flag found. Deleting paste...")
            result = privatebin().delete(paste[0], 'burnafterreading')
            if args.debug: print("Delete response:\t{}\n".format(result.decode("UTF-8")))

    else:
        print("Something went wrong...\nError:\t{}".format(result['message']))
        sys.exit(1)
