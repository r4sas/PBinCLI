import os
from base64 import b64decode, b64encode

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend


_BACKEND = default_backend()


def decrypt(pwd, json):
    iv = b64decode(json['iv'])
    ct = b64decode(json['ct'])
    salt = b64decode(json['salt'])
    ts = data['ts'] / 8

    tag_start = len(ct) - ts
    tag = ct[tag_start:]
    ciphertext = ct[:tag_start]

    mode_class = getattr(modes, json['mode'].upper())
    algo_class = getattr(algorithms, json['cipher'].upper())

    kdf = _kdf(json['ks'], iters=json['iter'], salt=salt)[0]
    key = kdf.derive(pwd)
    cipher = Cipher(algo_class(key),
                    mode_class(iv, tag, min_tag_length=ts),
                    backend=_BACKEND)

    dec = cipher.decryptor()
    result = dec.update(ciphertext) + dec.finalize()
    return result


def encrypt(pwd, plaintext, mode='gcm', algorithm='aes',
            keysize=256, tagsize=128, iters=256000):
    ts = tagsize / 8

    mode_class = getattr(modes, mode.upper())
    algo_class = getattr(algorithms, algorithm.upper())

    iv = os.urandom(16)
    kdf, salt = _kdf(keysize, iters)
    key = kdf.derive(pwd)
    cipher = Cipher(algo_class(key),
                    mode_class(iv, min_tag_length=ts),
                    backend=_BACKEND)

    enc = cipher.encryptor()
    ciphertext = enc.update(plaintext) + enc.finalize()

    json = {
        "v": 1,
        "iv": b64encode(iv),
        "salt": b64encode(salt),
        "ct": b64encode(ciphertext + enc.tag[:ts]),
        "iter": iters,
        "ks": keysize,
        "ts": tagsize,
        "mode": mode,
        "cipher": algorithm,
        "adata": ""
    }
    return json


def _kdf(keysize=256, iters=256000, salt=None, **kwargs):
    kdf_salt = salt or os.urandom(8)
    print("Salt: {}".format(kdf_salt))
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                     length=keysize / 8,
                     salt=kdf_salt,
                     iterations=iters,
                     backend=_BACKEND)

    return kdf, kdf_salt


if __name__ == "__main__":
    import json

    blob = '{"iv":"/6dKRRAOZ60oyumLMQsBtg==","v":1,"iter":256000,"ks":128,"ts":64,"mode":"gcm","adata":"","cipher":"aes","salt":"s8+LFcBmbcc=","ct":"wTapp5CWmD6SFA=="}'
    data = json.loads(blob)
    result = decrypt('pwd', data)
    assert result == "hi"

    print(decrypt('pwd', encrypt('pwd', result, tagsize=64)))
