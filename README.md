[![GitHub license](https://img.shields.io/github/license/r4sas/PBinCLI.svg)](https://github.com/r4sas/PBinCLI/blob/master/LICENSE)
[![GitHub tag](https://img.shields.io/github/tag/r4sas/PBinCLI.svg)](https://github.com/r4sas/PBinCLI/tags/)
[![Codacy Badge](https://app.codacy.com/project/badge/Grade/4f24f43356a84621bbd9078c4b3f1b70)](https://www.codacy.com/gh/r4sas/PBinCLI/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=r4sas/PBinCLI&amp;utm_campaign=Badge_Grade)

PBinCLI
=====

PBinCLI is command line client for [PrivateBin](https://github.com/PrivateBin/PrivateBin/) written on Python 3.

Installing
=====

Installation inside `virtualenv`:
```bash
python3 -m virtualenv --python=python3 venv
. venv/bin/activate
pip install pbincli
```

Installation to system with pip3:
```bash
pip3 install pbincli
```

*Note: if you used installation with `virtualenv`, don't forget to activate it before usage: call `. /path/to/venv/bin/activate` in terminal*

Configuration
=====

By default pbincli configured to use `https://paste.i2pd.xyz/` for sending and receiving pastes. No proxy used by default.

You can create config file to use different settings.

Configuration file is searched in `~/.config/pbincli/pbincli.conf`, `%APPDATA%/pbincli/pbincli.conf` (Windows) and `~/Library/Application Support/pbincli/pbincli.conf` (MacOS)

Example contents
-----

```ini
server=https://paste.i2pd.xyz/
proxy=http://127.0.0.1:3128
```

All possible options for configuration file
-----

| Option               | Default                 | Possible value |
|----------------------|-------------------------|----------------|
| server               | https://paste.i2pd.xyz/ | Domain ending with slash |
| mirrors              | None                    | Domains separated with comma, like `http://privatebin.ygg/,http://privatebin.i2p/` |
| proxy                | None                    | Proxy address starting with scheme `http://` or `socks5://` |
| short                | False                   | True / False |
| short_api            | None                    | `tinyurl`, `clckru`, `isgd`, `vgd`, `cuttly`, `yourls`, `custom` |
| short_url            | None                    | Domain name of shortener service for `yourls`, or sortener URL (with required parameters) for `custom` |
| short_user           | None                    | Used only in `yourls` |
| short_pass           | None                    | Used only in `yourls` |
| short_token          | None                    | Used only in `yourls` |
| no_check_certificate | False                   | True / False |
| no_insecure_warning  | False                   | True / False |

Usage
=====

Tool available by command `pbincli`, help for every command can be called with `-h` option:
```bash
pbincli {send|get|delete} -h
```

Sending
-----

* Sending text:
```bash
pbincli send -t "Hello! This is test paste!"
```

* Use stdin input to read text for paste:
```bash
pbincli send - <<EOF
Hello! This is test paste!
EOF
```

* Sending file with text in paste:
```bash
pbincli send -f info.pdf -t "I'm sending my document."
```

* Sending only file without any text:
```bash
pbincli send -q -f info.pdf
```

*Note*: It is possible to set-up paste parameters such as burning after reading, expiritaion time, formatting, enabling discussions, and changing compression algorithm. Please refer to `pbincli send -h` output for more information.

Receiving
-----

To retrieve paste from server, use `get` command with paste info.

It must be formated like `pasteID#Passphrase` or use full URL to paste. Example:
```bash
pbincli get xxx#yyy                        ### receive paste xxx from https://paste.i2pd.xyz/ by default
pbincli get https://example.com/?xxx#yyy   ### receive paste xxx from https://example.com/
```

Deletion
-----

To delete paste from server, use `delete` command with required `-p` and `-t` options:
```bash
pbincli delete -p xxx -t deletetoken
```

If you need to delete paste on different server that configured, use `-s` option with instance URL.

Additional examples
=====

Here you can find additional examples.

Usage with service available inside I2P
-----

Change settings to use server `http://privatebin.i2p/` and proxy `http://127.0.0.1:4444`. Here's example for configuration file:
```ini
server=http://privatebin.i2p/
proxy=http://127.0.0.1:4444
```

Using tool with aliases
-----

Example of alias to send paste from `stdin` direclty to I2P service:
```bash
alias pastei2p="echo 'paste the text to stdin' && pbincli send -s http://privatebin.i2p/ -x http://127.0.0.1:4444 -"
```

Call it by running `pastei2p` in terminal.

License
=====

This project is licensed under the MIT license, which can be found in the file [LICENSE](https://github.com/r4sas/PBinCLI/blob/master/LICENSE) in the root of the project source code.
