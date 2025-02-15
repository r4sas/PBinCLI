

.. image:: https://img.shields.io/github/license/r4sas/PBinCLI.svg
   :target: https://github.com/r4sas/PBinCLI/blob/master/LICENSE
   :alt: GitHub license


.. image:: https://img.shields.io/github/tag/r4sas/PBinCLI.svg
   :target: https://github.com/r4sas/PBinCLI/tags/
   :alt: GitHub tag


.. image:: https://app.codacy.com/project/badge/Grade/4f24f43356a84621bbd9078c4b3f1b70
   :target: https://www.codacy.com/gh/r4sas/PBinCLI/dashboard?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=r4sas/PBinCLI&amp;utm_campaign=Badge_Grade
   :alt: Codacy Badge


PBinCLI
=======

PBinCLI is a command line client for `PrivateBin <https://github.com/PrivateBin/PrivateBin/>`_ written in Python 3.

Installation
============

Installing globally using pip3:

.. code-block:: bash

   pip3 install pbincli

Installing with ``virtualenv``\ :

.. code-block:: bash

   python3 -m virtualenv --python=python3 venv
   . venv/bin/activate
   pip install pbincli

*Note*\ : if you used ``virtualenv`` installation method, don't forget to activate your virtual environment before running the tool: call ``. /path/to/venv/bin/activate`` in terminal

Configuration
=============

By default PBinCLI is configured to use ``https://paste.i2pd.xyz/`` for sending and receiving pastes. No proxy is used by default.

You can always create a config file to use different settings.

Configuration file is expected to be found in ``~/.config/pbincli/pbincli.conf``\ , ``%APPDATA%/pbincli/pbincli.conf`` (Windows) and ``~/Library/Application Support/pbincli/pbincli.conf`` (MacOS)

Example of config file content
------------------------------

.. code-block:: ini

   server=https://paste.i2pd.xyz/
   proxy=http://127.0.0.1:3128

List of OPTIONS available
-------------------------

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Possible value
   * - server
     - https://paste.i2pd.xyz/
     - Domain ending with slash
   * - random_server
     - None
     - Domains separated with comma, selected randomly
   * - mirrors
     - None
     - Domains separated with comma, like ``http://privatebin.ygg/,http://privatebin.i2p/``
   * - proxy
     - None
     - Proxy address starting with scheme ``http://`` or ``socks5://``
   * - expire
     - 1day
     - 5min / 10min / 1hour / 1day / 1week / 1month / 1year / never
   * - burn
     - False
     - True / False
   * - discus
     - False
     - True / False
   * - format
     - plaintext
     - plaintext / syntaxhighlighting / markdown
   * - short
     - False
     - True / False
   * - short_api
     - None
     - ``tinyurl``\ , ``clckru``\ , ``isgd``\ , ``vgd``\ , ``cuttly``\ , ``yourls``\ , ``custom``
   * - short_url
     - None
     - Domain name of shortener service for ``yourls``\ , or URL (with required parameters) for ``custom``
   * - short_user
     - None
     - Used only in ``yourls``
   * - short_pass
     - None
     - Used only in ``yourls``
   * - short_token
     - None
     - Used only in ``yourls``
   * - output
     - None
     - Path to the directory where the received data will be saved
   * - no_check_certificate
     - False
     - True / False
   * - no_insecure_warning
     - False
     - True / False
   * - compression
     - zlib
     - zlib / none
   * - auth
     - None
     - ``basic``\ , ``custom``
   * - auth_user
     - None
     - Basic authorization username
   * - auth_pass
     - None
     - Basic authorization password
   * - auth_custom
     - None
     - Custom authorization headers in JSON format, like ``{'Authorization': 'Bearer token'}``
   * - json
     - False
     - Print sending result in JSON format


Usage
=====

PBinCLI tool is started with ``pbincli`` command. Detailed help on command usage is provided with ``-h`` option:

.. code-block:: bash

   pbincli {send|get|delete} -h

Sending
-------


* 
  Sending text:

  .. code-block:: bash

     pbincli send -t "Hello! This is a test paste!"

* 
  Using stdin input to read text into a paste:

  .. code-block:: bash

     pbincli send - <<EOF
     Hello! This is a test paste!
     EOF

* 
  Sending a file with text attached into a paste:

  .. code-block:: bash

     pbincli send -f info.pdf -t "I'm sending my document."

* 
  Sending a file only with no text attached:

  .. code-block:: bash

     pbincli send -q -f info.pdf

Other options
^^^^^^^^^^^^^

It is also possible to set-up paste parameters such as "burn after reading", expiritaion time, formatting, enabling discussions and changing compression algorithm. Please refer to ``pbincli send -h`` output for more information.

Receiving
---------

To retrieve a paste from a server, you need to use ``get`` command with the paste info.

Paste info must be formated as ``pasteID#Passphrase`` or just use full URL to a paste. Example:

.. code-block:: bash

   pbincli get "xxx#yyy"                        ### receive paste xxx from https://paste.i2pd.xyz/ by default
   pbincli get "https://example.com/?xxx#yyy"   ### receive paste xxx from https://example.com/

Deletion
--------

To delete a paste from a server, use ``delete`` command with paste info:

.. code-block:: bash

   pbincli delete "pasteid=xxx&deletetoken=yyy"                        ### delete paste xxx from https://paste.i2pd.xyz/ by default
   pbincli delete "https://example.com/?pasteid=xxx&deletetoken=yyy"   ### delete paste xxx from https://example.com/

If you need to delete a paste on different server than the configured one, use ``-s`` option together with the instance URL.

Additional examples
===================

Here you can find additional examples.

Usage with I2P enabled services
-------------------------------

Change settings to set server to ``http://privatebin.i2p/`` and proxy to ``http://127.0.0.1:4444``. Configuration file for this example is:

.. code-block:: ini

   server=http://privatebin.i2p/
   proxy=http://127.0.0.1:4444

Using aliases
-------------

Example of alias to send a paste from ``stdin`` direclty to I2P service:

.. code-block:: bash

   alias pastei2p="echo 'paste the text to stdin' && pbincli send -s http://privatebin.i2p/ -x http://127.0.0.1:4444 -"

Call it by running ``pastei2p`` in terminal.

License
=======

This project is licensed under the MIT license, which can be found in the file `LICENSE <https://github.com/r4sas/PBinCLI/blob/master/LICENSE>`_ in the root of the project source code.
