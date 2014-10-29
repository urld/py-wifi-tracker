from collections import OrderedDict
import datetime
import json
import logging
import os.path

import requests

log = logging.getLogger(__name__)
logging.getLogger('requests').setLevel(logging.WARNING)


class ProbeRequest(object):

    def __init__(self, source_mac, capture_dts,
                 target_ssid=None, signal_strength=None):
        self.capture_dts = capture_dts
        self.source_mac = source_mac
        self.target_ssid = target_ssid
        self.signal_strength = signal_strength

    def __str__(self):
        return "SENDER='{}', SSID='{}', RSSi={}".format(self.source_mac,
                                                        self.target_ssid,
                                                        self.signal_strength)

    def __jdict__(self):
        return OrderedDict([('source_mac', self.source_mac),
                            ('capture_dts', datetime.datetime.strftime(self.capture_dts,
                                                                       '%Y-%m-%d %H:%M:%S.%f')),
                            ('target_ssid', self.target_ssid),
                            ('signal_strength', self.signal_strength)])


class Device(object):

    def __init__(self, device_mac, last_seen_dts=None, known_ssids=None,
                 vendor_company=None, vendor_country=None):
        self.device_mac = device_mac
        self.known_ssids = known_ssids if known_ssids else []
        self.vendor_company = vendor_company
        self.vendor_country = vendor_country
        self.last_seen_dts = last_seen_dts

    def _lookup_vendor(self):
        lookup_url = 'https://www.macvendorlookup.com/api/v2/' + self.device_mac
        try:
            vendor_response = requests.get(lookup_url).json()[0]
        except Exception as e:
            log.error("Unable to lookup vendor.", e)
            raise e
        else:
            return vendor_response

    def set_vendor(self):
        try:
            vendor = self._lookup_vendor()
            self.vendor_company = vendor['company']
            self.vendor_country = vendor['country']
        except:
            self.vendor_company = None
            self.vendor_country = None

    def add_ssid(self, ssid):
        if ssid and ssid not in self.known_ssids:
            self.known_ssids.append(ssid)
            log.debug('SSID added to device:{}'.format(ssid))

    def __str__(self):
        return "MAC='{}', vendor='{} [{}]'".format(self.device_mac,
                                                   self.vendor_company,
                                                   self.vendor_country)

    def __jdict__(self):
        return OrderedDict([('device_mac', self.device_mac),
                            ('known_ssids', self.known_ssids),
                            ('last_seen_dts', datetime.datetime.strftime(self.last_seen_dts,
                                                                         '%Y-%m-%d %H:%M:%S.%f')),
                            ('vendor_company', self.vendor_company),
                            ('vendor_country', self.vendor_country)])


class Tracker(object):

    def __init__(self, storage_dir):
        self.storage_dir = storage_dir
        self.request_filename = os.path.join(self.storage_dir, 'requests')

    def add_request(self, request):
        # TODO: store in mongodb/send over REST
        self._write_request(request)

    def _write_request(self, request):
        dump = json_compact(request)
        with open(self.request_filename, 'a') as file:
            file.write('\n' + dump)

    def get_devices(self, load_dts=None, oui_lookup=True):
        if not load_dts:
            load_dts = datetime.datetime.now()
        requests = self._read_requests(load_dts)
        devices = {}
        for request in requests:
            id = request.source_mac
            capture_dts = request.capture_dts
            if id not in devices:
                devices[id] = Device(id, last_seen_dts=capture_dts)
                if oui_lookup:
                    devices[id].set_vendor()
                log.debug("new device created: {}".format(devices[id]))
            devices[id].add_ssid(request.target_ssid)
            if devices[id].last_seen_dts < capture_dts:
                devices[id].last_seen_dts = capture_dts
        return devices

    def _read_requests(self, load_dts):
        with open(self.request_filename) as file:
            raw = file.readlines()
        all = [_load_request(r.rstrip('\n')) for r in raw if len(r) > 1]
        for x in all:
            if type(None) == type(x.capture_dts):
                print x.__dict__
        print load_dts
        return [e for e in all if e.capture_dts < load_dts]


def _load_request(dump):
    decoded = json.loads(dump)
    try:
        capture_dts = datetime.datetime.strptime(decoded['capture_dts'],
                                                 '%Y-%m-%d %H:%M:%S.%f')
    except:
        capture_dts = None
    request = ProbeRequest(decoded['source_mac'], capture_dts,
                           target_ssid=decoded['target_ssid'],
                           signal_strength=decoded['signal_strength'])
    return request


def json_pretty(obj):
    return json.dumps(obj.__jdict__(), indent=4, separators=(',', ': '))


def json_compact(obj):
    return json.dumps(obj.__jdict__(), separators=(',', ':'))
