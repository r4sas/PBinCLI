from sys import exit
from pbincli.format import Paste

def send(args, api_client):
    if not args.notext:
        if args.text:
            text = args.text
        elif args.stdin:
            text = args.stdin.read()
    elif not args.file:
        print("Nothing to send!")
        exit(1)
    else:
        text = ""

    paste = Paste(args.debug)
    paste.setVersion(api_client.getVersion())
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

    if args.debug: print("Request:\t{}".format(request))

    # If we use dry option, exit now
    if args.dry: exit(0)

    result = api_client.post(request)

    if args.debug: print("Response:\t{}\n".format(result))

    if 'status' in result and not result['status']:
        passphrase = paste.getHash()

        print("Paste uploaded!\nPasteID:\t{}\nPassword:\t{}\nDelete token:\t{}\n\nLink:\t\t{}?{}#{}".format(
            result['id'],
            passphrase,
            result['deletetoken'],
            api_client.server,
            result['id'],
            passphrase))
    elif 'status' in result and result['status']:
        print("Something went wrong...\nError:\t\t{}".format(result['message']))
        exit(1)
    else:
        print("Something went wrong...\nError: Empty response.")
        exit(1)


def get(args, api_client):
    from pbincli.utils import check_writable

    try:
        pasteid, passphrase = args.pasteinfo.split("#")
    except ValueError as err:
        print("PBinCLI error: provided info hasn't contain valid PasteID#Passphrase string")
        exit(1)

    if not (pasteid and passphrase):
        print("PBinCLI error: Incorrect request")
        exit(1)

    if args.debug: print("PasteID:\t{}\nPassphrase:\t{}".format(pasteid, passphrase))

    paste = Paste()

    if args.password:
        paste.setPassword(args.password)
        if args.debug: print("Password:\t{}".format(password))

    result = api_client.get(pasteid)

    if args.debug: print("Response:\t{}\n".format(result))

    if 'status' in result and not result['status']:
        print("Paste received!")

        version = result['v'] if 'v' in result else 1
        paste.setVersion(version)
        
        if version == 2:
            if args.debug: print("Message:\t{}\nAuthentication data:\t{}".format(result['ct'], result['adata']))

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
                f.close

        attachment, attachment_name = paste.getAttachment()

        if attachment:
            print("Found file, attached to paste. Saving it to {}\n".format(attachment_name))

            check_writable(attachment_name)
            with open(attachment_name, "wb") as f:
                f.write(attachment)
                f.close

        if version == 1 and 'meta' in result and 'burnafterreading' in result['meta'] and result['meta']['burnafterreading']:
            print("Burn afrer reading flag found. Deleting paste...")
            result = api_client.delete(json_encode({'pasteid':pasteid,'deletetoken':'burnafterreading'}))

            if args.debug: print("Delete response:\t{}\n".format(result))

            if 'status' in result and not result['status']:
                print("Paste successfully deleted!")
            elif 'status' in result and result['status']:
                print("Something went wrong...\nError:\t\t{}".format(result['message']))
                exit(1)
            else:
                print("Something went wrong...\nError: Empty response.")
                exit(1)

    elif 'status' in result and result['status']:
        print("Something went wrong...\nError:\t\t{}".format(result['message']))
        exit(1)
    else:
        print("Something went wrong...\nError: Empty response.")
        exit(1)


def delete(args, api_client):
    from pbincli.utils import json_encode

    pasteid = args.paste
    token = args.token

    if args.debug: print("PasteID:\t{}\nToken:\t\t{}".format(pasteid, token))

    result = api_client.delete(json_encode({'pasteid':pasteid,'deletetoken':token}))

    if args.debug: print("Response:\t{}\n".format(result))

    if 'status' in result and not result['status']:
        print("Paste successfully deleted!")
    elif 'status' in result and result['status']:
        print("Something went wrong...\nError:\t\t{}".format(result['message']))
        exit(1)
    else:
        print("Something went wrong...\nError: Empty response.")
        exit(1)
