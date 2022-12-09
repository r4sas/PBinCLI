import signal, sys
from urllib.parse import parse_qsl

from pbincli.api import Shortener
from pbincli.format import Paste
from pbincli.utils import PBinCLIError, check_writable, json_encode, uri_validator, validate_url_ending


def signal_handler(sig, frame):
    print('Keyboard interrupt received, terminating…')
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


def send(args, api_client, settings=None):
    if args.short:
        shortener = Shortener(settings)

    if not args.notext:
        if args.text:
            text = args.text
        elif args.stdin:
            print("Reading text from stdin…")
            text = args.stdin.read()
    elif not args.file:
        PBinCLIError("Nothing to send!")
    else:
        text = ""

    print("Preparing paste…")
    paste = Paste(args.debug)

    if args.verbose: print("Used server: {}".format(api_client.getServer()))

    # get from server supported paste format version and update object
    if args.verbose: print("Getting supported paste format version from server…")
    version = api_client.getVersion()
    paste.setVersion(version)

    if args.verbose: print("Filling paste with data…")
    # set compression type, works only on v2 pastes
    if version == 2:
        paste.setCompression(args.compression)

    # add text in paste (if it provided)
    paste.setText(text)

    # If we set PASSWORD variable
    if args.password:
        paste.setPassword(args.password)

    # If we set FILE variable
    if args.file:
        paste.setAttachment(args.file)

    if args.verbose: print("Encrypting paste…")
    paste.encrypt(
        formatter = args.format,
        burnafterreading = args.burn,
        discussion = args.discus,
        expiration = args.expire)

    if args.verbose: print("Sending request to server…")
    request = paste.getJSON()

    if args.debug: print("Passphrase:\t{}\nRequest:\t{}".format(paste.getHash(), request))

    # If we use dry option, exit now
    if args.dry: sys.exit(0)

    print("Uploading paste…")
    result = api_client.post(request)

    if args.debug: print("Response:\t{}\n".format(result))

    # Paste was sent. Checking for returned status code
    if not result['status']: # return code is zero
        passphrase = paste.getHash()

        # Paste information
        print("Paste uploaded!\nPasteID:\t{}\nPassword:\t{}\nDelete token:\t{}".format(
            result['id'],
            passphrase,
            result['deletetoken']))

        # Paste link
        print("\nLink:\t\t{}?{}#{}".format(
            settings['server'],
            result['id'],
            passphrase))

        # Paste deletion link
        print("Delete Link:\t{}?pasteid={}&deletetoken={}".format(
            settings['server'],
            result['id'],
            result['deletetoken']))

        # Print links to mirrors if present
        if settings['mirrors']:
            print("\nMirrors:")
            urls = settings['mirrors'].split(',')
            for x in urls:
                print("\t\t{}?{}#{}".format(
                    validate_url_ending(x),
                    result['id'],
                    passphrase))

    elif result['status']: # return code is other then zero
        PBinCLIError("Something went wrong…\nError:\t\t{}".format(result['message']))
    else: # or here no status field in response or it is empty
        PBinCLIError("Something went wrong…\nError: Empty response.")

    if args.short:
        print("\nQuerying URL shortening service…")
        shortener.getlink("{}?{}#{}".format(
            settings['server'],
            result['id'],
            passphrase))


def get(args, api_client, settings=None):
    parseduri, isuri = uri_validator(args.pasteinfo)

    if isuri and parseduri.query and parseduri.fragment:
        api_client.server = args.pasteinfo.split("?")[0]
        pasteid = parseduri.query
        passphrase = parseduri.fragment
    elif parseduri.path and parseduri.path != "/" and parseduri.fragment:
        pasteid = parseduri.path
        passphrase = parseduri.fragment
    else:
        PBinCLIError("Provided info hasn't contain valid URL or PasteID#Passphrase string")

    if args.verbose: print("Used server: {}".format(api_client.getServer()))
    if args.debug: print("PasteID:\t{}\nPassphrase:\t{}".format(pasteid, passphrase))

    paste = Paste(args.debug)

    if args.password:
        paste.setPassword(args.password)
        if args.debug: print("Password:\t{}".format(args.password))

    if args.verbose: print("Requesting paste from server…")
    result = api_client.get(pasteid)

    if args.debug: print("Response:\t{}\n".format(result))

    # Paste was received. Checking received status code
    if not result['status']: # return code is zero
        print("Paste received! Decoding…")

        version = result['v'] if 'v' in result else 1
        paste.setVersion(version)

        if version == 2:
            if args.debug: print("Authentication data:\t{}".format(result['adata']))

        paste.setHash(passphrase)
        paste.loadJSON(result)
        paste.decrypt()

        text = paste.getText()

        if args.debug: print("Decoded text size: {}\n".format(len(text)))

        if len(text):
            if args.debug: print("{}\n".format(text.decode()))
            filename = "paste-" + pasteid + ".txt"
            print("Found text in paste. Saving it to {}".format(filename))

            check_writable(filename)
            with open(filename, "wb") as f:
                f.write(text)
                f.close()

        attachment, attachment_name = paste.getAttachment()

        if attachment:
            print("Found file, attached to paste. Saving it to {}\n".format(attachment_name))

            check_writable(attachment_name)
            with open(attachment_name, "wb") as f:
                f.write(attachment)
                f.close()

        if version == 1 and 'meta' in result and 'burnafterreading' in result['meta'] and result['meta']['burnafterreading']:
            print("Burn afrer reading flag found. Deleting paste…")
            api_client.delete(json_encode({'pasteid':pasteid,'deletetoken':'burnafterreading'}))

    elif result['status']: # return code is other then zero
        PBinCLIError("Something went wrong…\nError:\t\t{}".format(result['message']))
    else: # or here no status field in response or it is empty
        PBinCLIError("Something went wrong…\nError: Empty response.")


def delete(args, api_client, settings=None):
    parseduri, isuri = uri_validator(args.pasteinfo)

    if isuri:
        api_client.server = args.pasteinfo.split("?")[0]
        query = dict(parse_qsl(parseduri.query))
    else:
        query = dict(parse_qsl(args.pasteinfo))

    if 'pasteid' in query and 'deletetoken' in query:
        pasteid = query['pasteid']
        token = query['deletetoken']
    else:
        PBinCLIError("Provided info hasn't contain required information")

    if args.verbose: print("Used server: {}".format(api_client.getServer()))
    if args.debug: print("PasteID:\t{}\nToken:\t\t{}".format(pasteid, token))

    print("Requesting paste deletion…")
    api_client.delete(json_encode({'pasteid':pasteid,'deletetoken':token}))
