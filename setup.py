#!/usr/bin/env python

from distutils.core import setup
from wifitracker import __version__

with open('README.rst') as readme:
    readme = readme.read()  # reading the readme (haha)

setup(
    name='wifi-tracker',
    version=__version__,
    description='tool to track wifi devices based on their probe requests',
    long_description=readme,
    author='David Url',
    author_email='david@x00.at',
    url='',
    packages=[
        'wifitracker',
    ],
    package_dir={'wifitracker': 'wifitracker'},
    package_data={'wifitracker': ['logging.conf']},
    py_modules=[
        'docopt',
    ],
    scripts=[
        'wifi-tracker',
    ],
    requires=[
        'scapy (>=2.1.0)',
    ],
    license='GNU General Public License v3 or later (GPLv3+)',
    keywords='smartmeter, data analysis, wiener netze',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'Intended Audience :: Telecommunications Industry',
        'License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Operating System :: POSIX',   # is it?
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Topic :: Security',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking',
        'Topic :: Utilities',
    ],
)
