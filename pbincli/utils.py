import json, ntpath, os, sys

class PBinCLIException(Exception):
    pass


def PBinCLIError(message):
    print("PBinCLI Error: {}".format(message), file=sys.stderr)
    exit(1)


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def check_readable(f):
    # Checks if path exists and readable
    if not os.path.exists(f) or not os.access(f, os.R_OK):
        PBinCLIError("Error accessing path: {}".format(f))


def check_writable(f):
    # Checks if path is writable
    if not os.access(os.path.dirname(f) or ".", os.W_OK):
        PBinCLIError("Path is not writable: {}".format(f))


def json_encode(s):
    return json.dumps(s, separators=(',',':')).encode()


def validate_url(s):
    if not s.endswith('/'):
        s = s + "/"
    return s
