#!/usr/bin/env python

from setuptools import setup

with open("README.md") as readme:
    long_description = readme.read()

with open("requirements.txt") as f:
    install_requires = f.read().split()

setup(
    name='PBinCLI',
    version='0.1',
    description='PrivateBin client for command line',
    long_description=long_description,
    author='R4SAS',
    author_email='r4sas@i2pmail.org',
    url='https://github.com/r4sas/PBinCLI',
    keywords='privatebin',
    license='DWTFYWWI',
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: Other/Proprietary License',
        'Programming Language :: Python :: 3',
        'Environment :: Console',
    ],
    packages=['pbincli'],
    install_requires=install_requires,
    entry_points={
        'console_scripts': [
            'pbincli=pbincli.cli:main',
        ],
    }
)
