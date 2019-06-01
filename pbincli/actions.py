import json, hashlib, os, sys
import pbincli.actions
from sjcl import SJCL

from base64 import b64encode, b64decode
from pbincli.utils import PBinCLIException

def send(args, api_client):
    from pbincli.utils import check_readable, compress, path_leaf
    from mimetypes import guess_type

    if not args.notext:
        if args.text:
            text = args.text
        elif args.stdin:
            text = args.stdin.read()
    elif not args.file:
        print("Nothing to send!")
        sys.exit(1)
    else:
        text = ""

    # Formatting request
    request = {'expire':args.expire,'formatter':args.format,'burnafterreading':int(args.burn),'opendiscussion':int(args.discus)}

    passphrase = b64encode(os.urandom(32))
    if args.debug: print("Passphrase:\t{}".format(passphrase))

    # If we set PASSWORD variable
    if args.password:
        digest = hashlib.sha256(args.password.encode("UTF-8")).hexdigest()
        password = passphrase + digest.encode("UTF-8")
    else:
        password = passphrase

    if args.debug: print("Password:\t{}".format(password))

    # Encrypting text
    cipher = SJCL().encrypt(compress(text.encode('utf-8')), password, mode='gcm')

    # TODO: should be implemented in upstream
    for k in ['salt', 'iv', 'ct']: cipher[k] = cipher[k].decode()

    request['data'] = json.dumps(cipher, ensure_ascii=False).replace(' ','')

    # If we set FILE variable
    if args.file:
        check_readable(args.file)
        with open(args.file, "rb") as f:
            contents = f.read()
            f.close()
        mime = guess_type(args.file, strict=False)[0]

        # MIME fallback
        if not mime: mime = "application/octet-stream"

        if args.debug: print("Filename:\t{}\nMIME-type:\t{}".format(path_leaf(args.file), mime))

        file = "data:" + mime[0] + ";base64," + b64encode(contents).decode()
        filename = path_leaf(args.file)

        cipherfile = SJCL().encrypt(compress(file.encode('utf-8')), password, mode='gcm')
        # TODO: should be implemented in upstream
        for k in ['salt', 'iv', 'ct']: cipherfile[k] = cipherfile[k].decode()
        cipherfilename = SJCL().encrypt(compress(filename.encode('utf-8')), password, mode='gcm')
        for k in ['salt', 'iv', 'ct']: cipherfilename[k] = cipherfilename[k].decode()

        request['attachment'] = json.dumps(cipherfile, ensure_ascii=False).replace(' ','')
        request['attachmentname'] = json.dumps(cipherfilename, ensure_ascii=False).replace(' ','')

    if args.debug: print("Request:\t{}".format(request))

    # If we use dry option, exit now
    if args.dry: sys.exit(0)

    result = api_client.post(request)

    if args.debug: print("Response:\t{}\n".format(result))

    try:
        result = json.loads(result)
    except ValueError as e:
        print("PBinCLI Error: {}".format(e))
        sys.exit(1)

    if 'status' in result and not result['status']:
        print("Paste uploaded!\nPasteID:\t{}\nPassword:\t{}\nDelete token:\t{}\n\nLink:\t\t{}?{}#{}".format(result['id'], passphrase.decode(), result['deletetoken'], api_client.server, result['id'], passphrase.decode()))
    elif 'status' in result and result['status']:
        print("Something went wrong...\nError:\t\t{}".format(result['message']))
        sys.exit(1)
    else:
        print("Something went wrong...\nError: Empty response.")
        sys.exit(1)


def get(args, api_client):
    from pbincli.utils import check_writable, decompress

    pasteid, passphrase = args.pasteinfo.split("#")

    if pasteid and passphrase:
        if args.debug: print("PasteID:\t{}\nPassphrase:\t{}".format(pasteid, passphrase))

        if args.password:
            digest = hashlib.sha256(args.password.encode("UTF-8")).hexdigest()
            password = passphrase + digest.encode("UTF-8")
        else:
            password = passphrase

        if args.debug: print("Password:\t{}".format(password))

        result = api_client.get(pasteid)
    else:
        print("PBinCLI error: Incorrect request")
        sys.exit(1)

    if args.debug: print("Response:\t{}\n".format(result))

    try:
        result = json.loads(result)
    except ValueError as e:
        print("PBinCLI Error: {}".format(e))
        sys.exit(1)

    if 'status' in result and not result['status']:
        print("Paste received! Text inside:")
        data = json.loads(result['data'])

        if args.debug: print("Text:\t{}\n".format(data))

        text = SJCL().decrypt(data, password)

        if args.debug: print("Decoded text size: {}\n".format(len(text)))

        if len(text):
            print("{}\n".format(decompress(text.decode())))

            check_writable("paste.txt")
            with open("paste.txt", "wb") as f:
                f.write(decompress(text.decode()))
                f.close

        if 'attachment' in result and 'attachmentname' in result:
            print("Found file, attached to paste. Decoding it and saving")

            cipherfile = json.loads(result['attachment']) 
            cipherfilename = json.loads(result['attachmentname'])

            if args.debug: print("Name:\t{}\nData:\t{}".format(cipherfilename, cipherfile))

            attachmentf = SJCL().decrypt(cipherfile, password)
            attachmentname = SJCL().decrypt(cipherfilename, password)

            attachment = decompress(attachmentf.decode('utf-8')).decode('utf-8').split(',', 1)[1]
            file = b64decode(attachment)
            filename = decompress(attachmentname.decode('utf-8')).decode('utf-8')

            print("Filename:\t{}\n".format(filename))

            check_writable(filename)
            with open(filename, "wb") as f:
                f.write(file)
                f.close

        if 'burnafterreading' in result['meta'] and result['meta']['burnafterreading']:
            print("Burn afrer reading flag found. Deleting paste...")
            result = api_client.delete(pasteid, 'burnafterreading')

            if args.debug: print("Delete response:\t{}\n".format(result))

            try:
                result = json.loads(result)
            except ValueError as e:
                print("PBinCLI Error: {}".format(e))
                sys.exit(1)

            if 'status' in result and not result['status']:
                print("Paste successfully deleted!")
            elif 'status' in result and result['status']:
                print("Something went wrong...\nError:\t\t{}".format(result['message']))
                sys.exit(1)
            else:
                print("Something went wrong...\nError: Empty response.")
                sys.exit(1)

    elif 'status' in result and result['status']:
        print("Something went wrong...\nError:\t\t{}".format(result['message']))
        sys.exit(1)
    else:
        print("Something went wrong...\nError: Empty response.")
        sys.exit(1)


def delete(args, api_client):
    pasteid = args.paste
    token = args.token

    if args.debug: print("PasteID:\t{}\nToken:\t\t{}".format(pasteid, token))

    result = api_client.delete(pasteid, token)

    if args.debug: print("Response:\t{}\n".format(result))

    try:
        result = json.loads(result)
    except ValueError as e:
        print("PBinCLI Error: {}".format(e))
        sys.exit(1)
    
    if 'status' in result and not result['status']:
        print("Paste successfully deleted!")
    elif 'status' in result and result['status']:
        print("Something went wrong...\nError:\t\t{}".format(result['message']))
        sys.exit(1)
    else:
        print("Something went wrong...\nError: Empty response.")
        sys.exit(1)
