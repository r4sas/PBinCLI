import json, hashlib, ntpath, sys, zlib
import pbincli.actions
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import HMAC, SHA256
from Crypto.Cipher import AES

from base64 import b64encode, b64decode
from base58 import b58encode, b58decode
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
    return zlib.decompress(s, -zlib.MAX_WBITS)

def compress(s):
    # using compressobj as compress doesn't let us specify wbits
    # needed to get the raw stream without headers
    co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
    b = co.compress(s) + co.flush()
    return b

def send(args, api_client):
    if args.text:
        text = args.text
    elif args.stdin:
        text = args.stdin.read()
    elif args.file:
        text = "Sending a file to you!"
    else:
        print("Nothing to send!")
        sys.exit(1)

    # Decryption key consists of some random bytes (base64 or base58 encoded in URL hash) and an optional user defined password
    password = get_random_bytes(CIPHER_BLOCK_BYTES)

    # If we set PASSWORD variable
    if args.password:
        password += args.password

    passphrase = b58encode(password)
    if args.debug: print("Passphrase:\t{}\nPassword:\t{}".format(passphrase, password))

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
    if args.debug: print("Authenticated data:\t{}".format(adata))

    cipher_message = {'paste':text}
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
    if args.debug: print("Cipher message:\t{}".format(json_encode(cipher_message)))

    # Encrypting message and optional file
    cipher = AES.new(key, AES.MODE_GCM, nonce=iv, mac_len=CIPHER_TAG_BYTES)
    cipher.update(json_encode(adata))
    ciphertext, tag = cipher.encrypt_and_digest(compress(json_encode(cipher_message)))

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

        password = b58decode(passphrase)
        if args.password:
            password += args.password

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
        print("Paste received!")
        if args.debug: print("Message:\t{}\nAuthentication data:\t{}".format(result['ct'], result['adata']))

        # Key derivation, using PBKDF2 and SHA256 HMAC
        iv = b64decode(result['adata'][0][0])
        salt = b64decode(result['adata'][0][1])
        key = PBKDF2(password, salt, dkLen=CIPHER_BLOCK_BYTES, count=CIPHER_ITERATION_COUNT, prf=lambda password, salt: HMAC.new(password, salt, SHA256).digest())

        # Decrypting message
        cipher = AES.new(key, AES.MODE_GCM, nonce=iv, mac_len=CIPHER_TAG_BYTES)
        cipher.update(json_encode(result['adata']))
        # Cut the cipher text into message and tag
        cipher_text_tag = b64decode(result['ct'])
        cipher_text = cipher_text_tag[:-CIPHER_TAG_BYTES]
        cipher_tag = cipher_text_tag[-CIPHER_TAG_BYTES:]
        cipher_message = json.loads(decompress(cipher.decrypt_and_verify(cipher_text, cipher_tag)))
        if args.debug: print("{}\n".format(cipher_message))

        check_writable("paste.txt")
        with open("paste.txt", "wb") as f:
            f.write(cipher_message['paste'].encode())
            f.close

        if 'attachment' in cipher_message and 'attachment_name' in cipher_message:
            print("Found file, attached to paste. Decoding it and saving")

            if args.debug: print("Name:\t{}\nData:\t{}".format(cipher_message['attachment_name'], cipher_message['attachment']))

            file = b64decode(cipher_message['attachment'].split(',', 1)[1])

            check_writable(cipher_message['attachment_name'])
            with open(cipher_message['attachment_name'], "wb") as f:
                f.write(file)
                f.close

        # burn after reading via API, only required for PrivateBin < 1.2
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
