import json, ntpath, os, zlib
from base64 import b64encode, b64decode

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


def decompress(s, ver = 1):
    if ver == 2:
        return zlib.decompress(s, -zlib.MAX_WBITS)
    else:
        return zlib.decompress(bytearray(map(ord, b64decode(s.encode('utf-8')).decode('utf-8'))), -zlib.MAX_WBITS)


def compress(s, ver = 1):
    if ver == 2:
        # using compressobj as compress doesn't let us specify wbits
        # needed to get the raw stream without headers
        co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        return co.compress(s) + co.flush()
    else:
        co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
        b = co.compress(s) + co.flush()
        return b64encode(''.join(map(chr, b)).encode('utf-8'))


def json_encode(s):
    return json.dumps(s, separators=(',',':')).encode()
