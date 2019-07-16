#!/usr/bin/env python

from setuptools import setup
from pbincli.__init__ import __version__ as pbincli_version

with open("README.rst") as readme:
    long_description = readme.read()

with open("requirements.txt") as f:
    install_requires = f.read().split()

setup(
    name='PBinCLI',
    version=pbincli_version,
    description='PrivateBin client for command line',
    long_description=long_description,
    long_description_content_type='text/x-rst',
    author='R4SAS',
    author_email='r4sas@i2pmail.org',
    url='https://github.com/r4sas/PBinCLI',
    keywords='privatebin cryptography security',
    license='MIT',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Environment :: Console',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Topic :: Security :: Cryptography',
        'Topic :: Utilities',
    ],
    packages=['pbincli'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'pbincli=pbincli.cli:main',
        ],
    }
)
