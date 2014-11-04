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
        dts = datetime.datetime.strftime(self.capture_dts,
                                         '%Y-%m-%d %H:%M:%S.%f')
        return OrderedDict([('source_mac', self.source_mac),
                            ('capture_dts', dts),
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

    def set_vendor(self):
        try:
            vendor = _lookup_vendor(self.device_mac)
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
        dts = datetime.datetime.strftime(self.last_seen_dts,
                                         '%Y-%m-%d %H:%M:%S.%f')
        return OrderedDict([('device_mac', self.device_mac),
                            ('known_ssids', self.known_ssids),
                            ('last_seen_dts', dts),
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
                log.debug("new device created: {}".format(devices[id]))
            devices[id].add_ssid(request.target_ssid)
            if devices[id].last_seen_dts < capture_dts:
                devices[id].last_seen_dts = capture_dts
        if oui_lookup:
            # this is done in parallel for all devices:
            set_vendors(devices)
        return devices

    def _read_requests(self, load_dts):
        with open(self.request_filename) as file:
            raw = file.readlines()
        all = [_load_request(r.rstrip('\n')) for r in raw if len(r) > 1]
        return [e for e in all if e.capture_dts < load_dts]


def _load_request(dump):
    decoded = json.loads(dump)
    try:
        capture_dts = _strptime(decoded['capture_dts'])
    except:
        capture_dts = None
    target_ssid = decoded['target_ssid']
    if target_ssid is not None:
        target_ssid = repr(target_ssid)[2:-1]
    request = ProbeRequest(decoded['source_mac'], capture_dts,
                           target_ssid=target_ssid,
                           signal_strength=decoded['signal_strength'])
    return request


def _strptime(s):
    return datetime.datetime(year=int(s[:4]),
                             month=int(s[5:7]),
                             day=int(s[8:10]),
                             hour=int(s[11:13]),
                             minute=int(s[14:16]),
                             second=int(s[17:19]),
                             microsecond=int(s[20:26]))


def json_pretty(obj):
    return json.dumps(obj.__jdict__(), indent=4, separators=(',', ': '))


def json_compact(obj):
    return json.dumps(obj.__jdict__(), separators=(',', ':'))


def _lookup_vendor(device_mac, session=None):
    lookup_url = 'http://www.macvendorlookup.com/api/v2/' + device_mac
    try:
        if not session:
            vendor_response = requests.get(lookup_url, timeout=20).json()[0]
        else:
            vendor_response = session.get(lookup_url, timeout=20).json()[0]
    except Exception as e:
        log.error("Unable to lookup vendor.", e.msg)
        raise e
    else:
        return vendor_response


from threading import Thread
from time import sleep


class LookupThread(Thread):

    def __init__(self, device, session):
        super(LookupThread, self).__init__()
        self.device = device
        self.session = session

    def run(self):
        self.device.set_vendor()


def set_vendors(devices, interval=2, slots=100):
    def alive_count(lst):
        alive_list = map(lambda x: 1 if x.isAlive() else 0, lst)
        # enable the following line if you want to see a funny stuff:
        # print alive_list
        return reduce(lambda a, b: a+b, alive_list)
    session = requests.Session()
    threads = [LookupThread(devices[id], session) for id in devices]
    free = slots
    i = 0
    n = len(threads)
    for i in range(i, n):
        threads[i].start()
        free -= 1
        # wait for free slots:
        while free <= 0:
            sleep(interval)
            free = slots - alive_count(threads)
    # wait for threads:
    while alive_count(threads) > 0:
        sleep(interval)
