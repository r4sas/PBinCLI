#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Edited SJCL.py library (https://github.com/berlincode/sjcl/)
for AES.MODE_GCM support, work begin.
 
pip3.5 install pycryptodome
"""

from Crypto.Hash import SHA256, HMAC
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
import base64


def truncate_iv(iv, ol, tlen):  # ol and tlen in bits
    ivl = len(iv)  # iv length in bytes
    ol = (ol - tlen) // 8

    # "compute the length of the length" (see gcm.js)
    L = 2
    while (L < 4) and ((ol >> (8*L))) > 0:
        L += 1
    if L < 15 - ivl:
        L = 15 - ivl

    return iv[:(15-L)]


def check_mode_gcm():
    # checks if pycrypto has support for gcm
    try:
        AES.MODE_GCM
    except:
        raise Exception(
            "Pycrypto does not seem to support MODE_gcm. " +
            "You need a version >= 2.7a1 (or a special branch)."
        )


class SJCL(object):

    def __init__(self):
        self.salt_size = 8  # bytes
        self.tag_size = 16  # bytes
        self.mac_size = 16  # bytes; mac = message authentication code (MAC)
        self.prf = lambda p, s: HMAC.new(p, s, SHA256).digest()

    def decrypt(self, data, passphrase):
        check_mode_gcm()  # check gcm support

        if data["cipher"] != "aes":
            raise Exception("only aes cipher supported")
        print(data["mode"])
        if data["mode"] != "gcm":
            raise Exception("unknown mode(!=gcm)")

        if data["adata"] != "":
            raise Exception("additional authentication data not equal ''")

        if data["v"] != 1:
            raise Exception("only version 1 is currently supported")

        if data["ts"] != self.tag_size * 8:
            raise Exception("desired tag length != %d" % (self.tag_size * 8))

        salt = base64.b64decode(data["salt"])

    #    print "salt", hex_string(salt)
        if len(salt) != self.salt_size:
            raise Exception("salt should be %d bytes long" % self.salt_size)

        dkLen = data["ks"]//8
        if dkLen != 16:
            raise Exception("key length should be 16 bytes")

        key = PBKDF2(
            passphrase,
            salt,
            count=data['iter'],
            dkLen=dkLen,
            prf=self.prf
        )
#        print "key", hex_string(key)

        ciphertext = base64.b64decode(data["ct"])
        iv = base64.b64decode(data["iv"])
#        print AES.block_size

        nonce = truncate_iv(iv, len(ciphertext)*8, data["ts"])

        # split tag from ciphertext (tag was simply appended to ciphertext)
        mac = ciphertext[-(data["ts"]//8):]
#        print len(ciphertext)
        ciphertext = ciphertext[:-(data["ts"]//8)]
#        print len(ciphertext)
#        print len(tag)

#        print "len", len(nonce)
        cipher = AES.new(key, AES.MODE_GCM, nonce)
        plaintext = cipher.decrypt(ciphertext)
        print(mac)
#        cipher.verify(mac)

        return plaintext

    def encrypt(self, plaintext, passphrase, count=10000, dkLen=32):
        # dkLen = key length in bytes

        check_mode_gcm()  # check gcm support

        salt = get_random_bytes(self.salt_size)
        iv = get_random_bytes(16)  # TODO dkLen?

        key = PBKDF2(passphrase, salt, count=count, dkLen=dkLen, prf=self.prf)

        # TODO plaintext padding?
        nonce = truncate_iv(iv, len(plaintext) * 8, self.tag_size * 8)
    #    print len(nonce)

        cipher = AES.new(
            key,
            AES.MODE_GCM,
            nonce,
            mac_len=self.mac_size
        )

        ciphertext = cipher.encrypt(plaintext)
        mac = cipher.digest()

        ciphertext = ciphertext + mac

        return {
            "salt": base64.b64encode(salt),
            "iter": count,
            "ks": dkLen*8,
            "ct": base64.b64encode(ciphertext),
            "iv": base64.b64encode(iv),
            "cipher": "aes",
            "mode": "gcm",
            "adata": "",
            "v": 1,
            "ts": self.tag_size * 8
            }
