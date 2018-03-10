PBinCLI
=====

#### [PrivateBin](https://github.com/PrivateBin/PrivateBin/) CLI (in development)

This CLI tool currently working only with compression-disabled services (see [that](https://github.com/PrivateBin/PrivateBin/issues/188#issuecomment-281284360) issue).

```patch
--- a/js/privatebin.js
+++ b/js/privatebin.js
@@ -545,9 +545,9 @@ jQuery.PrivateBin = (function($, sjcl, Base64, RawDeflate) {
             };

             if ((password || '').trim().length === 0) {
-                return sjcl.encrypt(key, compress(message), options);
+                return sjcl.encrypt(key, message, options);
             }
-            return sjcl.encrypt(key + sjcl.codec.hex.fromBits(sjcl.hash.sha256.hash(password)), compress(message), options);
+            return sjcl.encrypt(key + sjcl.codec.hex.fromBits(sjcl.hash.sha256.hash(password)), message, options);
         };

         /**
@@ -564,10 +564,10 @@ jQuery.PrivateBin = (function($, sjcl, Base64, RawDeflate) {
         {
             if (data !== undefined) {
                 try {
-                    return decompress(sjcl.decrypt(key, data));
+                    return sjcl.decrypt(key, data);
                 } catch(err) {
                     try {
-                        return decompress(sjcl.decrypt(key + sjcl.codec.hex.fromBits(sjcl.hash.sha256.hash(password)), data));
+                        return sjcl.decrypt(key + sjcl.codec.hex.fromBits(sjcl.hash.sha256.hash(password)), data);
                     } catch(e) {
                         return '';
                     }
```

Currenty compression disabled on next services:

* https://paste.i2pd.xyz/
* https://paste.r4sas.i2p/
* *here can be your service*

Installing
-----
```bash
$ virtualenv --python=python3 venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

Usage
-----
Edit variables `server`, `proxies` and `useproxy` in `pbincli/settings.py` to your values.

Run inside `venv` command:

    $ ./cli send -c "Hello!"

Or use stdin input to read text for paste:

    $ ./cli send - <<EOF
    Hello!
    This is test paste!
    EOF

It will send string `Hello!` to PrivateBin.

To send file use `--file` or `-f` with filename. Example:

    $ ./cli send -c "My document" -f info.pdf


To retrieve paste from server, use `get` command with paste info.

It must be formated like `pasteID#passphrase`. Example:

    $ ./cli get 49eeb1326cfa9491#vfeortoVWaYeJlviDdhxQBtj5e0I2kArpynrtu/tnGs=

More info you can find by typing

    $ ./cli [-h] {send, get, delete}

License
-------
This project is licensed under the DWTFYWWI license, which can be found in the file
[LICENSE](LICENSE) in the root of the project source code.
