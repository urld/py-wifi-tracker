from collections import OrderedDict
import datetime
import json
import logging
import os.path

import requests
from scapy.all import Dot11ProbeReq

log = logging.getLogger(__name__)


def _extract_rssi(packet):
    """Extract the RSSi (received signal strength indicator) from a wifi packet.
    """
    try:
        extra = packet.notdecoded
        signal_strength = -(256 - ord(extra[-4:-3]))
    except Exception as e:
        print e
        signal_strength = None
    return signal_strength


def _extract_ssid(packet):
    """Extract the SSID (service set identifier) from a captured wifi packet.
    """
    ssid = packet.getlayer(Dot11ProbeReq).info
    if len(ssid) < 1:
        ssid = None
    try:
        ssid = str(ssid)
    except:
        ssid = None
    return ssid


class ProbeRequest(object):

    def __init__(self, packet):
        self.capture_dts = datetime.datetime.now()
        self.target_mac = packet.addr3.lower()
        self.target_ssid = _extract_ssid(packet)
        self.source_mac = packet.addr2.lower()
        self.signal_strength = _extract_rssi(packet)

    def _get_id(self):
        return self.source_mac + str(self.capture_dts)

    def _get_type(self):
        return 'ProbeRequest'

    def __str__(self):
        return "SENDER='{}', SSID='{}', RSSi={}".format(self.source_mac,
                                                        self.target_ssid,
                                                        self.signal_strength)


class Device(object):

    def __init__(self, request):
        now = datetime.datetime.now()
        self.device_mac = request.source_mac
        self.known_ssids = []
        self.lookup_vendor()
        self.last_seen_dts = now
        self.modify_dts = now

    def _request_vendor(self):
        lookup_url = 'https://www.macvendorlookup.com/api/v2/' + self.device_mac
        try:
            vendor_response = requests.get(lookup_url).json()[0]
        except Exception as e:
            log.error("Unable to lookup vendor.", e)
            raise e
        else:
            return vendor_response

    def lookup_vendor(self):
        try:
            vendor = self._request_vendor()
            self.vendor_company = vendor['company']
            self.vendor_country = vendor['country']
        except:
            self.vendor_company = None
            self.vendor_country = None

    def add_ssid(self, ssid):
        if ssid and ssid not in self.known_ssids:
            self.known_ssids.append(ssid)
            self.modify_dts = datetime.datetime.now()

    def update_last_seen_dts(self):
        self.last_seen_dts = datetime.datetime.now()

    def _get_id(self):
        return self.device_mac

    def _get_type(self):
        return 'Device'

    def __str__(self):
        return "MAC='{}', vendor='{} [{}]'".format(self.device_mac,
                                                   self.vendor_company,
                                                   self.vendor_country)

    def __odict__(self):
        return OrderedDict([('device_mac', self.device_mac),
                            ('known_ssids', self.known_ssids),
                            ('last_seen_dts', str(self.last_seen_dts)),
                            ('vendor_company', self.vendor_company),
                            ('vendor_country', self.vendor_country)])

    def dump_json(self, dump_dir):
        filename = os.path.join(dump_dir, 'dev_{}.json'.format(self._get_id()))
        with open(filename, 'w') as file:
            json.dump(self.__odict__(),
                      file,
                      indent=4,
                      separators=(',', ': '))


class Storage(object):

    def __init__(self):
        self.storage = {}

    def add(self, document):
        id = document._get_id()
        type = document._get_type()
        key = _make_key(type, id)
        self.storage[key] = document

    def get(self, type, id):
        key = _make_key(type, id)
        return self.storage[key]

    def has(self, type, id):
        key = _make_key(type, id)
        if key in self.storage:
            return True
        else:
            return False


def _make_key(type, id):
    return str(type) + str(id)
