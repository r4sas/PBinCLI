from pbincli.format import Paste
from pbincli.utils import PBinCLIError

def send(args, api_client, settings=None):
    from pbincli.api import Shortener
    if args.short:
        shortener = Shortener(settings)

    if not args.notext:
        if args.text:
            text = args.text
        elif args.stdin:
            text = args.stdin.read()
    elif not args.file:
        PBinCLIError("Nothing to send!")
    else:
        text = ""

    paste = Paste(args.debug)

    # get from server supported paste format version and update object
    version = api_client.getVersion()
    paste.setVersion(version)

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

    paste.encrypt(
        formatter = args.format,
        burnafterreading = args.burn,
        discussion = args.discus,
        expiration = args.expire)

    request = paste.getJSON()

    if args.debug:
        print("Passphrase:\t{}".format(paste.getHash()))
        print("Request:\t{}".format(request))

    # If we use dry option, exit now
    if args.dry: exit(0)

    result = api_client.post(request)

    if args.debug: print("Response:\t{}\n".format(result))

    # Paste was sent. Checking for returned status code
    if not result['status']: # return code is zero
        passphrase = paste.getHash()

        print("Paste uploaded!\nPasteID:\t{}\nPassword:\t{}\nDelete token:\t{}\n\nLink:\t\t{}?{}#{}".format(
            result['id'],
            passphrase,
            result['deletetoken'],
            settings['server'],
            result['id'],
            passphrase))
    elif result['status']: # return code is other then zero
        PBinCLIError("Something went wrong...\nError:\t\t{}".format(result['message']))
    else: # or here no status field in response or it is empty
        PBinCLIError("Something went wrong...\nError: Empty response.")

    if args.short:
        print("\nQuerying URL shortening service...")
        shortener.getlink("{}?{}#{}".format(
            settings['server'],
            result['id'],
            passphrase))


def get(args, api_client, settings=None):
    from pbincli.utils import check_writable, json_encode

    try:
        pasteid, passphrase = args.pasteinfo.split("#")
    except ValueError:
        PBinCLIError("Provided info hasn't contain valid PasteID#Passphrase string")

    if not (pasteid and passphrase):
        PBinCLIError("Incorrect request")

    if args.debug: print("PasteID:\t{}\nPassphrase:\t{}".format(pasteid, passphrase))

    paste = Paste(args.debug)

    if args.password:
        paste.setPassword(args.password)
        if args.debug: print("Password:\t{}".format(args.password))

    result = api_client.get(pasteid)

    if args.debug: print("Response:\t{}\n".format(result))

    # Paste was received. Checking received status code
    if not result['status']: # return code is zero
        print("Paste received!")

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
            print("Burn afrer reading flag found. Deleting paste...")
            api_client.delete(json_encode({'pasteid':pasteid,'deletetoken':'burnafterreading'}))

    elif result['status']: # return code is other then zero
        PBinCLIError("Something went wrong...\nError:\t\t{}".format(result['message']))
    else: # or here no status field in response or it is empty
        PBinCLIError("Something went wrong...\nError: Empty response.")


def delete(args, api_client, settings=None):
    from pbincli.utils import json_encode

    pasteid = args.paste
    token = args.token

    if args.debug: print("PasteID:\t{}\nToken:\t\t{}".format(pasteid, token))

    api_client.delete(json_encode({'pasteid':pasteid,'deletetoken':token}))
