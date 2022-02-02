

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

PBinCLI is command line client for `PrivateBin <https://github.com/PrivateBin/PrivateBin/>`_ written on Python 3.

Installing
==========

Installation inside ``virtualenv``\ :

.. code-block:: bash

   python3 -m virtualenv --python=python3 venv
   . venv/bin/activate
   pip install pbincli

Installation to system with pip3:

.. code-block:: bash

   pip3 install pbincli

*Note*\ : if you used installation with ``virtualenv``\ , don't forget to activate it before usage: call ``. /path/to/venv/bin/activate`` in terminal

Configuration
=============

By default pbincli configured to use ``https://paste.i2pd.xyz/`` for sending and receiving pastes. No proxy used by default.

You can create config file to use different settings.

Configuration file is searched in ``~/.config/pbincli/pbincli.conf``\ , ``%APPDATA%/pbincli/pbincli.conf`` (Windows) and ``~/Library/Application Support/pbincli/pbincli.conf`` (MacOS)

Example contents
----------------

.. code-block:: ini

   server=https://paste.i2pd.xyz/
   proxy=http://127.0.0.1:3128

All possible options for configuration file
-------------------------------------------

.. list-table::
   :header-rows: 1

   * - Option
     - Default
     - Possible value
   * - server
     - https://paste.i2pd.xyz/
     - Domain ending with slash
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
   * - no_check_certificate
     - False
     - True / False
   * - no_insecure_warning
     - False
     - True / False
   * - compression
     - zlib
     - zlib / none


Usage
=====

Tool available by command ``pbincli``\ , help for every command can be called with ``-h`` option:

.. code-block:: bash

   pbincli {send|get|delete} -h

Sending
-------


* 
  Sending text:

  .. code-block:: bash

     pbincli send -t "Hello! This is test paste!"

* 
  Use stdin input to read text for paste:

  .. code-block:: bash

     pbincli send - <<EOF
     Hello! This is test paste!
     EOF

* 
  Sending file with text in paste:

  .. code-block:: bash

     pbincli send -f info.pdf -t "I'm sending my document."

* 
  Sending only file without any text:

  .. code-block:: bash

     pbincli send -q -f info.pdf

Other options
^^^^^^^^^^^^^

It is possible to set-up paste parameters such as burning after reading, expiritaion time, formatting, enabling discussions, and changing compression algorithm. Please refer to ``pbincli send -h`` output for more information.

Receiving
---------

To retrieve paste from server, use ``get`` command with paste info.

It must be formated like ``pasteID#Passphrase`` or use full URL to paste. Example:

.. code-block:: bash

   pbincli get xxx#yyy                        ### receive paste xxx from https://paste.i2pd.xyz/ by default
   pbincli get https://example.com/?xxx#yyy   ### receive paste xxx from https://example.com/

Deletion
--------

To delete paste from server, use ``delete`` command with required ``-p`` and ``-t`` options:

.. code-block:: bash

   pbincli delete -p xxx -t deletetoken

If you need to delete paste on different server that configured, use ``-s`` option with instance URL.

Additional examples
===================

Here you can find additional examples.

Usage with service available inside I2P
---------------------------------------

Change settings to use server ``http://privatebin.i2p/`` and proxy ``http://127.0.0.1:4444``. Here's example for configuration file:

.. code-block:: ini

   server=http://privatebin.i2p/
   proxy=http://127.0.0.1:4444

Using tool with aliases
-----------------------

Example of alias to send paste from ``stdin`` direclty to I2P service:

.. code-block:: bash

   alias pastei2p="echo 'paste the text to stdin' && pbincli send -s http://privatebin.i2p/ -x http://127.0.0.1:4444 -"

Call it by running ``pastei2p`` in terminal.

License
=======

This project is licensed under the MIT license, which can be found in the file `LICENSE <https://github.com/r4sas/PBinCLI/blob/master/LICENSE>`_ in the root of the project source code.
