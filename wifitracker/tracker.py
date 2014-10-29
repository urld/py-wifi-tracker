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

    def _get_type(self):
        return 'ProbeRequest'

    def __str__(self):
        return "SENDER='{}', SSID='{}', RSSi={}".format(self.source_mac,
                                                        self.target_ssid,
                                                        self.signal_strength)

    def __jdict__(self):
        return OrderedDict([('source_mac', self.source_mac),
                            ('capture_dts', str(self.capture_dts)),
                            ('target_ssid', self.target_ssid),
                            ('signal_strength', self.signal_strength)])


class Device(object):

    def __init__(self, device_mac, last_seen_dts=None, known_ssids=[],
                 vendor_company=None, vendor_country=None):
        self.device_mac = device_mac
        self.known_ssids = known_ssids
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
            log.debug('Appending SSID:{}'.format(ssid))

    def _get_type(self):
        return 'Device'

    def __str__(self):
        return "MAC='{}', vendor='{} [{}]'".format(self.device_mac,
                                                   self.vendor_company,
                                                   self.vendor_country)

    def __jdict__(self):
        return OrderedDict([('device_mac', self.device_mac),
                            ('known_ssids', self.known_ssids),
                            ('last_seen_dts', str(self.last_seen_dts)),
                            ('vendor_company', self.vendor_company),
                            ('vendor_country', self.vendor_country)])


class Tracker(object):

    def __init__(self, storage_dir):
        self.storage_dir = storage_dir
        self.request_filename = os.path.join(self.storage_dir, 'requests')
        self.locked = []

    def add_request(self, request):
        # add request to tracker
        self._write_request(request)
        # check if device is known:
        self.lock(request.source_mac)
        device = self.get_device(request.source_mac)
        if not device:
            # create new device if unknown:
            device = Device(request.source_mac)
            device.set_vendor()
            log.info("new device detected: {}".format(device))
            log.debug("FUCK {}: {}".format())
        # update device data:
        device.add_ssid(request.target_ssid)
        if device.last_seen_dts:
            if device.last_seen_dts < request.capture_dts:
                device.last_seen_dts = request.capture_dts
        else:
            device.last_seen_dts = request.capture_dts
        self._write_device(device)

    def get_device(self, device_mac):
        filename = 'device_{}.json'.format(device_mac.replace(':', '_'))
        filepath = os.path.join(self.storage_dir, filename)
        if not os.path.isfile(filepath):
            return None
        with open(filepath, 'r') as file:
            dump = json.load(file)
            try:
                last_seen_dts = datetime.datetime.strptime(
                    dump['last_seen_dts'],
                    '%Y-%m-%d %H:%M:%S.%f')
            except:
                last_seen_dts = None
            device = Device(dump['device_mac'],
                            last_seen_dts=last_seen_dts,
                            known_ssids=dump['known_ssids'],
                            vendor_company=dump['vendor_company'],
                            vendor_country=dump['vendor_country'])
            log.debug('Reading {}: {}'.format(device.device_mac, device.known_ssids))
            return device

    def _write_device(self, device):
        dump = json_pretty(device)
        filename = 'device_{}.json'.format(device.device_mac.replace(':', '_'))
        filepath = os.path.join(self.storage_dir, filename)
        with open(filepath, 'w') as file:
            file.write(dump)
        log.debug('Wrote {}: {}'.format(device.device_mac, device.known_ssids))

    def _write_request(self, request):
        dump = json_compact(request)
        with open(self.request_filename, 'a') as requests_file:
            requests_file.write('\n' + dump)

    def lock(self, device_mac):
        while device_mac in self.locked:
            pass
        self.locked.append(device_mac)

    def release(self, device_mac):
        try:
            self.locked.remove(device_mac)
        except ValueError:
            pass


def json_pretty(obj):
    return json.dumps(obj.__jdict__(), indent=4, separators=(',', ': '))


def json_compact(obj):
    return json.dumps(obj.__jdict__(), separators=(',', ':'))
