from base64 import b64encode, b64decode
from pbincli.utils import PBinCLIError
import zlib

# try import AES cipher and check if it has GCM mode (prevent usage of pycrypto)
try:
    from Crypto.Cipher import AES
    if not hasattr(AES, 'MODE_GCM'):
        try:
            from Cryptodome.Cipher import AES
            from Cryptodome.Random import get_random_bytes
        except ImportError:
            PBinCLIError("AES GCM mode is not found in imported crypto module.\n" +
                "That can happen if you have installed pycrypto.\n\n" +
                "We tried to import pycryptodomex but it is not available.\n" +
                "Please install it via pip, if you still need pycrypto, by running:\n" +
                "\tpip install pycryptodomex\n" +
                "... otherwise use separate python environment or uninstall pycrypto:\n" +
                "\tpip uninstall pycrypto")
    else:
        from Crypto.Random import get_random_bytes
except ImportError:
    try:
        from Cryptodome.Cipher import AES
        from Cryptodome.Random import get_random_bytes
    except ImportError:
        PBinCLIError("Unable import pycryptodome")


CIPHER_ITERATION_COUNT = 100000
CIPHER_SALT_BYTES = 8
CIPHER_BLOCK_BITS = 256
CIPHER_TAG_BITS = 128


class Paste:
    def __init__(self, debug=False):
        self._version = 2
        self._compression = 'zlib'
        self._data = ''
        self._text = ''
        self._attachment = ''
        self._attachment_name = ''
        self._password = ''
        self._debug = debug
        self._iteration_count = CIPHER_ITERATION_COUNT
        self._salt_bytes = CIPHER_SALT_BYTES
        self._block_bits = CIPHER_BLOCK_BITS
        self._tag_bits = CIPHER_TAG_BITS
        self._key = get_random_bytes(int(self._block_bits / 8))


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
            if (len(passphrase) % 4 != 0):
                PBinCLIError("Incorrect passphrase! Maybe you have stripped trailing \"=\"?")
            self._key = b64decode(passphrase)


    def __deriveKey(self, salt):
        try:
            from Crypto.Protocol.KDF import PBKDF2
            from Crypto.Hash import HMAC, SHA256
        except ModuleNotFoundError:
            try:
                from Cryptodome.Protocol.KDF import PBKDF2
                from Cryptodome.Hash import HMAC, SHA256
            except ImportError:
                PBinCLIError("Unable import pycryptodome")

        # Key derivation, using PBKDF2 and SHA256 HMAC
        return PBKDF2(
            self._key + self._password.encode(),
            salt,
            dkLen = int(self._block_bits / 8),
            count = self._iteration_count,
            prf = lambda password, salt: HMAC.new(
                password,
                salt,
                SHA256
            ).digest())


    @classmethod
    def __initializeCipher(self, key, iv, adata, tagsize):
        from pbincli.utils import json_encode

        cipher = AES.new(key, AES.MODE_GCM, nonce=iv, mac_len=tagsize)
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

        self._iteration_count = self._data['adata'][0][2]
        self._block_bits = self._data['adata'][0][3]
        self._tag_bits = self._data['adata'][0][4]
        cipher_tag_bytes = int(self._tag_bits / 8)

        key = self.__deriveKey(salt)

        # Get compression type from received paste
        self._compression = self._data['adata'][0][7]

        cipher = self.__initializeCipher(key, iv, self._data['adata'], cipher_tag_bytes)
        # Cut the cipher text into message and tag
        cipher_text_tag = b64decode(self._data['ct'])
        cipher_text = cipher_text_tag[:-cipher_tag_bytes]
        cipher_tag = cipher_text_tag[-cipher_tag_bytes:]
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

        if self._debug: print("[Enc] Starting encyptor…")
        if self._version == 2: self._encryptV2()
        else:                  self._encryptV1()


    def _encryptV2(self):
        from pbincli.utils import json_encode

        if self._debug: print("[Enc] Preparing IV, Salt…")
        iv = get_random_bytes(int(self._tag_bits / 8))
        salt = get_random_bytes(self._salt_bytes)
        if self._debug: print("[Enc] Deriving Key…")
        key = self.__deriveKey(salt)

        if self._debug: print("[Enc] Preparing aData and message…")
        # prepare encryption authenticated data and message
        adata = [
            [
                b64encode(iv).decode(),
                b64encode(salt).decode(),
                self._iteration_count,
                self._block_bits,
                self._tag_bits,
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

        if self._debug: print("[Enc] Encrypting message…")
        cipher = self.__initializeCipher(key, iv, adata, int(self._tag_bits /8 ))
        ciphertext, tag = cipher.encrypt_and_digest(self.__compress(json_encode(cipher_message)))

        if self._debug: print("PBKDF2 Key:\t{}\nCipherText:\t{}\nCipherTag:\t{}"
            .format(b64encode(key), b64encode(ciphertext), b64encode(tag)))

        self._data = {'v':2,'adata':adata,'ct':b64encode(ciphertext + tag).decode(),'meta':{'expire':self._expiration}}


    def _encryptV1(self):
        from sjcl import SJCL
        from pbincli.utils import json_encode

        self._data = {'expire':self._expiration,'formatter':self._formatter,
            'burnafterreading':int(self._burnafterreading),'opendiscussion':int(self._discussion)}

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
