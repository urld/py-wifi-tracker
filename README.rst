======
README
======

Track wifi devices based on their public probe requests.

Requirements
============

- tcpdump
- Python 2.7:
  
  - scapy 2.1.0
  - requests 2.4.3

Installation
============

Install dependencies (on debian in this case):

.. code-block:: console

    $ apt-get install tcpdump

Install required python libraries:

.. code-block:: console

    $ git clone git://github.com/kennethreitz/requests.git
    $ cd requests
    $ python setup.py install

    $ wget http://www.secdev.org/projects/scapy/files/scapy-latest.tar.gz
    $ tar xvzf scapy-latest.tar.gz
    $ cd scapy-2.1.0
    $ python setup.py install

Install wifi-tracker:

.. code-block:: console

    $ git clone git://github.com/durl/wifi-tracker.git
    $ cd wifi-tracker
    $ python setup.py install

Usage
=====

Setup:

Sniff probe requests on a wireless network interface 'wlan1':

.. code-block:: console

    $ wifi-tracker monitor wlan1 start
    $ wifi-tracker sniff wlan1

Kill sniffer:

.. code-block:: console

    $ wifi-tracker kill
    $ wifi-tracker monitor wlan1 stop

Analyze:

.. code-block:: console

    $ wifi-tracker show devices
    [
    {
        "device_mac": "9c:ad:97:22:fa:3a",
        "alias": null,
        "known_ssids": [
            "AirportNetwork",
            "AndroidAP"
        ],
        "last_seen_dts": "2014-12-23 10:11:22.301919",
        "vendor_company": "Hon Hai Precision Ind. Co.,Ltd.",
        "vendor_country": "CHINA"
    },
    {
        "device_mac": "f8:e0:79:92:a3:4b",
        "alias": null,
        "known_ssids": [],
        "last_seen_dts": "2014-12-25 11:14:51.124419",
        "vendor_company": "Motorola Mobility LLC",
        "vendor_country": "UNITED STATES"
    },
    ...
    ]

.. code-block:: console

    $ wifi-tracker show devices "9c:ad:97:22:fa:3a"
    [
    {
        "device_mac": "9c:ad:97:22:fa:3a",
        "alias": null,
        "known_ssids": [
            "AirportNetwork",
            "AndroidAP"
        ],
        "last_seen_dts": "2014-12-23 10:11:22.301919",
        "vendor_company": "Hon Hai Precision Ind. Co.,Ltd.",
        "vendor_country": "CHINA"
    }
    ]

.. code-block:: console

    $ wifi-tracker show stations "foo"
    [
    {
        "ssid": "foo",
        "associated_devices": [
            "b8:d6:12:2b:0a:27",
            "98:8d:f7:9a:51:b0",
            "6c:e9:03:2a:3a:a2"
        ]
    }
    ]

TODO/Known Issues
=================

- analyzing the data is very slow if more than 100.000 requests have been collected (which can be sooner than one might expect)
- little to none error handling
- unittests (at least for data analysis)
- log to stdout, write output to file, since json can not be processed with line based tools like grep
- lookup geo location of known SSIDs using WiGLE (see `wigle wifi geolocation (Python recipe) <http://code.activestate.com/recipes/578637-wigle-wifi-geolocation/>`_)
      
  - visualize devices known SSIDs on a map
  - select only most likely location if multiple accesspints exist
