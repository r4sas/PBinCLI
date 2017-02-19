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

Using
-----
Edit `self.server = 'http://paste.r4sas.i2p/'` in `pbincli/transports.py` to your server.
Run inside `venv` command `python pbincli.py send`. It will send string `Test!` to PrivateBin.
