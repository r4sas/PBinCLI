PBinCLI
=====

PrivateBin CLI (in development)

Installing
-----
```bash
$ virtualenv --python=python2.7 venv
$ . venv/bin/activate
$ pip install -r requirements.txt
```

Usage
-----
Edit variables `server`, `proxies` and `useproxy` in `pbincli/settings.py` to your values.

Run inside `venv` command:

	$ python pbincli.py send -c "Hello!"

It will send string `Hello!` to PrivateBin.

To send file use `--file` or `-f` with filename. Example:

	$ python pbincli.py send -c "My document" -f info.pdf

To retrieve paste from server, use `get` command with paste info.

It must be formated like `pasteID#passphrase`. Example:

	$ python pbincli.py get 49eeb1326cfa9491#vfeortoVWaYeJlviDdhxQBtj5e0I2kArpynrtu/tnGs=

More info you can find by typing

	$ python pbincli.py {send,get} -h

License
-------
This project is licensed under the DWTFYWWI license, which can be found in the file
LICENSE in the root of the project source code.
