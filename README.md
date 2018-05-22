PBinCLI
=====

#### [PrivateBin](https://github.com/PrivateBin/PrivateBin/) CLI

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

    $ ./cli send --text "Hello!"

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
