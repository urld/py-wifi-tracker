======
README
======

TODO

Installation
============

Install dependencies on debian::

    # apt-get install libssl-dev tcpdump iw
    # wget http://download.aircrack-ng.org/aircrack-ng-1.2-beta1.tar.gz
    # tar -zxvf aircrack-ng-1.2-beta1.tar.gz
    # cd aircrack-ng-1.2-beta1
    # make
    # make install

Install required python libraries::

    # git clone git://github.com/kennethreitz/requests.git
    # cd requests
    # python setup.py install

    # wget http://www.secdev.org/projects/scapy/files/scapy-latest.tar.gz
    # tar xvzf scapy-latest.tar.gz
    # cd scapy-2.1.0
    # python setup.py install

::

    $ pip install wifi-tracker

Requirements
============

* tcpdump
* airmon-ng
* Python:
** scapy 2.1.0
** requests

Usage
=====

Setup::
    $ sudo airmon-ng start wlan0

Sniff probe requests::

    $ wifi-tracker sniff mon0 --debug

Kill sniffer::

    $ sudo kill -9 <pid>

The pid is logged when wifi-tracker starts

Features
========

TODO

