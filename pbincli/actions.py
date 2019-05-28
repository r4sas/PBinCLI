import json, hashlib, ntpath, sys, zlib
import pbincli.actions
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import HMAC, SHA256
from Crypto.Cipher import AES

from base64 import b64encode, b64decode
from mimetypes import guess_type
from pbincli.utils import PBinCLIException, check_readable, check_writable, json_encode

# Cipher settings
CIPHER_ITERATION_COUNT = 100000
CIPHER_SALT_BYTES = 8
CIPHER_BLOCK_BITS = 256
CIPHER_BLOCK_BYTES = int(CIPHER_BLOCK_BITS/8)
CIPHER_TAG_BITS = int(CIPHER_BLOCK_BITS/2)
CIPHER_TAG_BYTES = int(CIPHER_TAG_BITS/8)


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def decompress(s):
    return zlib.decompress(bytearray(map(ord, b64decode(s.encode('utf-8')).decode('utf-8'))), -zlib.MAX_WBITS)

def compress(s):
    co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    b = co.compress(s) + co.flush()

    return b64encode(''.join(map(chr, b)).encode('utf-8'))

def send(args, api_client):
    if args.stdin:
        text = args.stdin.read()
    elif args.text:
        text = args.text
    elif args.file:
        text = "Sending a file to you!"
    else:
        print("Nothing to send!")
        sys.exit(1)

    # Decryption key consists of some random bytes (base64 or base58 encoded in URL hash) and an optional user defined password
    password = get_random_bytes(CIPHER_BLOCK_BYTES)
    passphrase = b64encode(password)
    if args.debug: print("Passphrase:\t{}".format(passphrase))

    # If we set PASSWORD variable
    if args.password:
        password += args.password.encode('utf-8')

    if args.debug: print("Password:\t{}".format(password))

    # Key derivation, using PBKDF2 and SHA256 HMAC
    salt = get_random_bytes(CIPHER_SALT_BYTES)
    key = PBKDF2(password, salt, dkLen=CIPHER_BLOCK_BYTES, count=CIPHER_ITERATION_COUNT, prf=lambda password, salt: HMAC.new(password, salt, SHA256).digest())

    # prepare encryption authenticated data and message
    iv = get_random_bytes(CIPHER_TAG_BYTES)
    adata = [
        [
            b64encode(iv).decode(),
            b64encode(salt).decode(),
            CIPHER_ITERATION_COUNT,
            CIPHER_BLOCK_BITS,
            CIPHER_TAG_BITS,
            'aes',
            'gcm',
            'zlib'
        ],
        args.format,
        int(args.burn),
        int(args.discus)
    ]
    cipher_message = {'paste':text}
    if args.debug: print("Authenticated data:\t{}".format(adata))

    # If we set FILE variable
    if args.file:
        check_readable(args.file)
        with open(args.file, "rb") as f:
            contents = f.read()
            f.close()
        mime = guess_type(args.file)
        if args.debug: print("Filename:\t{}\nMIME-type:\t{}".format(path_leaf(args.file), mime[0]))

        cipher_message['attachment'] = "data:" + mime[0] + ";base64," + b64encode(contents).decode()
        cipher_message['attachment_name'] = path_leaf(args.file)

    # Encrypting message and optional file
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv, mac_len=CIPHER_TAG_BYTES)
    cipher.update(json_encode(adata).encode())
    ciphertext, tag = cipher.encrypt_and_digest(compress(json_encode(cipher_message).encode()))

    # Formatting request
    request = json_encode({'v':2,'adata':adata,'ct':b64encode(ciphertext + tag).decode(),'meta':{'expire':args.expire}})

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
