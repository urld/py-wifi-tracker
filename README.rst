======
README
======

Track wifi devices based on their public probe requests.

Requirements
============

- tcpdump
- airmon-ng (or something else to put your wifi card in monitor mode)
- Python 2.7:
  - scapy 2.1.0
  - requests 2.4.3

Installation
============

Install dependencies (on debian in this case)::

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



Usage
=====

You should do all of this as privileged user, or the monitor device might not be accessible.

Setup::

    $ airmon-ng start wlan0

Sniff probe requests::

    $ wifi-tracker sniff mon0 --debug

Kill sniffer::

    $ wifi-tracker kill <pid>

Generate a list of tracked devices after some sniffing::

    $ wifi-tracker show

Features
========

TODO

