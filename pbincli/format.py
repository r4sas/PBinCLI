from Crypto.Random import get_random_bytes
from Crypto.Cipher import AES
from base64 import b64encode, b64decode
from pbincli.utils import PBinCLIError
import zlib

CIPHER_ITERATION_COUNT = 100000
CIPHER_SALT_BYTES = 8
CIPHER_BLOCK_BITS = 256
CIPHER_BLOCK_BYTES = int(CIPHER_BLOCK_BITS/8)
CIPHER_TAG_BITS = int(CIPHER_BLOCK_BITS/2)
CIPHER_TAG_BYTES = int(CIPHER_TAG_BITS/8)

class Paste:
    def __init__(self, debug=False):
        self._version = 2
        self._compression = 'zlib'
        self._data = ''
        self._text = ''
        self._attachment = ''
        self._attachment_name = ''
        self._key = get_random_bytes(CIPHER_BLOCK_BYTES)
        self._password = ''
        self._debug = debug


    def setVersion(self, version):
        if self._debug: print("Set paste version to {}".format(version))
        self._version = version


    def setPassword(self, password):
        self._password = password


    def setText(self, text):
        self._text = text


    def setAttachment(self, path):
        from pbincli.utils import check_readable, path_leaf
        from mimetypes import guess_type

        check_readable(path)
        with open(path, 'rb') as f:
            contents = f.read()
            f.close()
        mime = guess_type(path, strict=False)[0]

        # MIME fallback
        if not mime: mime = 'application/octet-stream'

        if self._debug: print("Filename:\t{}\nMIME-type:\t{}".format(path_leaf(path), mime))

        self._attachment = 'data:' + mime + ';base64,' + b64encode(contents).decode()
        self._attachment_name = path_leaf(path)

    def setCompression(self, comp):
        self._compression = comp


    def getText(self):
        return self._text


    def getAttachment(self):
        return [b64decode(self._attachment.split(',', 1)[1]), self._attachment_name] \
            if self._attachment \
            else [False,False]


    def getJSON(self):
        if self._version == 2:
            from pbincli.utils import json_encode
            return json_encode(self._data).decode()
        else:
            return self._data


    def loadJSON(self, data):
        self._data = data


    def getHash(self):
        if self._version == 2:
            from base58 import b58encode
            return b58encode(self._key).decode()
        else:
            return b64encode(self._key).decode()


    def setHash(self, passphrase):
        if self._version == 2:
            from base58 import b58decode
            self._key = b58decode(passphrase)
        else:
            self._key = b64decode(passphrase)


    def __deriveKey(self, salt):
        from Crypto.Protocol.KDF import PBKDF2
        from Crypto.Hash import HMAC, SHA256

        # Key derivation, using PBKDF2 and SHA256 HMAC
        return PBKDF2(
            self._key + self._password.encode(),
            salt,
            dkLen = CIPHER_BLOCK_BYTES,
            count = CIPHER_ITERATION_COUNT,
            prf = lambda password, salt: HMAC.new(
                password,
                salt,
                SHA256
            ).digest())


    @classmethod
    def __initializeCipher(self, key, iv, adata):
        from pbincli.utils import json_encode

        cipher = AES.new(key, AES.MODE_GCM, nonce=iv, mac_len=CIPHER_TAG_BYTES)
        cipher.update(json_encode(adata))
        return cipher


    def __preparePassKey(self):
        from hashlib import sha256

        if self._password:
            digest = sha256(self._password.encode("UTF-8")).hexdigest()
            return b64encode(self._key) + digest.encode("UTF-8")
        else:
            return b64encode(self._key)


    def __decompress(self, s):
        if self._version == 2 and self._compression == 'zlib':
            # decompress data
            return zlib.decompress(s, -zlib.MAX_WBITS)
        elif self._version == 2 and self._compression == 'none':
            # nothing to do, just return original data
            return s
        elif self._version == 1:
            return zlib.decompress(bytearray(map(lambda c:ord(c)&255, b64decode(s.encode('utf-8')).decode('utf-8'))), -zlib.MAX_WBITS)
        else:
            PBinCLIError('Unknown compression type provided in paste!')


    def __compress(self, s):
        if self._version == 2 and self._compression == 'zlib':
            # using compressobj as compress doesn't let us specify wbits
            # needed to get the raw stream without headers
            co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
            return co.compress(s) + co.flush()
        elif self._version == 2 and self._compression == 'none':
            # nothing to do, just return original data
            return s
        elif self._version == 1:
            co = zlib.compressobj(wbits=-zlib.MAX_WBITS)
            b = co.compress(s) + co.flush()
            return b64encode(''.join(map(chr, b)).encode('utf-8'))
        else:
            PBinCLIError('Unknown compression type provided!')


    def decrypt(self):
        # that is wrapper which running needed function regrading to paste version
        if self._version == 2: self._decryptV2()
        else:                  self._decryptV1()


    def _decryptV2(self):
        from json import loads as json_decode
        iv = b64decode(self._data['adata'][0][0])
        salt = b64decode(self._data['adata'][0][1])
        key = self.__deriveKey(salt)

        # Get compression type from received paste
        self._compression = self._data['adata'][0][7]

        cipher = self.__initializeCipher(key, iv, self._data['adata'])
        # Cut the cipher text into message and tag
        cipher_text_tag = b64decode(self._data['ct'])
        cipher_text = cipher_text_tag[:-CIPHER_TAG_BYTES]
        cipher_tag = cipher_text_tag[-CIPHER_TAG_BYTES:]
        cipher_message = json_decode(self.__decompress(cipher.decrypt_and_verify(cipher_text, cipher_tag)).decode())

        self._text = cipher_message['paste'].encode()

        if 'attachment' in cipher_message and 'attachment_name' in cipher_message:
            self._attachment = cipher_message['attachment']
            self._attachment_name = cipher_message['attachment_name']


    def _decryptV1(self):
        from sjcl import SJCL
        from json import loads as json_decode

        password = self.__preparePassKey()
        cipher_text = json_decode(self._data['data'])
        if self._debug: print("Text:\t{}\n".format(cipher_text))

        text = SJCL().decrypt(cipher_text, password)

        if len(text):
            if self._debug: print("Decoded Text:\t{}\n".format(text))
            self._text = self.__decompress(text.decode())

        if 'attachment' in self._data and 'attachmentname' in self._data:
            cipherfile = json_decode(self._data['attachment'])
            cipherfilename = json_decode(self._data['attachmentname'])

            if self._debug: print("Name:\t{}\nData:\t{}".format(cipherfilename, cipherfile))

            attachment = SJCL().decrypt(cipherfile, password)
            attachmentname = SJCL().decrypt(cipherfilename, password)

            self._attachment = self.__decompress(attachment.decode('utf-8')).decode('utf-8')
            self._attachment_name = self.__decompress(attachmentname.decode('utf-8')).decode('utf-8')


    def encrypt(self, formatter, burnafterreading, discussion, expiration):
        # that is wrapper which running needed function regrading to paste version
        self._formatter = formatter
        self._burnafterreading = burnafterreading
        self._discussion = discussion
        self._expiration = expiration

        if self._version == 2: self._encryptV2()
        else:                  self._encryptV1()


    def _encryptV2(self):
        from pbincli.utils import json_encode

        iv = get_random_bytes(CIPHER_TAG_BYTES)
        salt = get_random_bytes(CIPHER_SALT_BYTES)
        key = self.__deriveKey(salt)

        # prepare encryption authenticated data and message
        adata = [
            [
                b64encode(iv).decode(),
                b64encode(salt).decode(),
                CIPHER_ITERATION_COUNT,
                CIPHER_BLOCK_BITS,
                CIPHER_TAG_BITS,
                'aes',
                'gcm',
                self._compression
            ],
            self._formatter,
            int(self._discussion),
            int(self._burnafterreading)
        ]
        cipher_message = {'paste':self._text}
        if self._attachment:
            cipher_message['attachment'] = self._attachment
            cipher_message['attachment_name'] = self._attachment_name

        cipher = self.__initializeCipher(key, iv, adata)
        ciphertext, tag = cipher.encrypt_and_digest(self.__compress(json_encode(cipher_message)))

        self._data = {'v':2,'adata':adata,'ct':b64encode(ciphertext + tag).decode(),'meta':{'expire':self._expiration}}


    def _encryptV1(self):
        from sjcl import SJCL
        from pbincli.utils import json_encode

        self._data = {'expire':self._expiration,'formatter':self._formatter,'burnafterreading':int(self._burnafterreading),'opendiscussion':int(self._discussion)}

        password = self.__preparePassKey()
        if self._debug: print("Password:\t{}".format(password))

        # Encrypting text
        cipher = SJCL().encrypt(self.__compress(self._text.encode('utf-8')), password, mode='gcm')
        for k in ['salt', 'iv', 'ct']: cipher[k] = cipher[k].decode()

        self._data['data'] = json_encode(cipher)

        if self._attachment:
            cipherfile = SJCL().encrypt(self.__compress(self._attachment.encode('utf-8')), password, mode='gcm')
            for k in ['salt', 'iv', 'ct']: cipherfile[k] = cipherfile[k].decode()

            cipherfilename = SJCL().encrypt(self.__compress(self._attachment_name.encode('utf-8')), password, mode='gcm')
            for k in ['salt', 'iv', 'ct']: cipherfilename[k] = cipherfilename[k].decode()

            self._data['attachment'] = json_encode(cipherfile)
            self._data['attachmentname'] = json_encode(cipherfilename)
