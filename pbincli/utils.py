import json, ntpath, os

class PBinCLIException(Exception):
    pass


def path_leaf(path):
    head, tail = ntpath.split(path)
    return tail or ntpath.basename(head)


def check_readable(f):
    # Checks if path exists and readable
    if not os.path.exists(f) or not os.access(f, os.R_OK):
        raise PBinCLIException("Error accessing path: {}".format(f))


def check_writable(f):
    # Checks if path is writable
    if not os.access(os.path.dirname(f) or ".", os.W_OK):
        raise PBinCLIException("Path is not writable: {}".format(f))


def json_encode(s):
    return json.dumps(s, separators=(',',':')).encode()
