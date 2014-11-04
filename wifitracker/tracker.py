from collections import OrderedDict
import datetime
import json
import logging
import os.path
from threading import Thread
from time import sleep

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

    def set_vendor(self, session=None):
        """Set the vendor of this device. The vendor can be looked up by the
        devices mac address.

        Keyword arguments:
        session -- HTTPS session with connections which should be reused for the
                   requests neccesary for the lookup.
        """
        try:
            vendor = _lookup_vendor(self.device_mac, session)
            self.vendor_company = vendor['company']
            self.vendor_country = vendor['country']
        except:
            self.vendor_company = None
            self.vendor_country = None

    def add_ssid(self, ssid):
        """Add a new SSID to the device.

        ssid -- string object
        """
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
        """Add the captured request to the tracker. The tracker might store this
        request in a file or database backend.
        """
        # TODO: store in mongodb/send over REST
        self._write_request(request)

    def _write_request(self, request):
        dump = json_compact(request)
        with open(self.request_filename, 'a') as file:
            file.write('\n' + dump)

    def get_devices(self, load_dts=None):
        """Load a version of all devices valid at the given timestamp."""
        if not load_dts:
            load_dts = datetime.datetime.now()
        requests = self._read_requests(load_dts)
        devices = {}
        for request in requests:
            id = request.source_mac
            capture_dts = request.capture_dts
            ssid = request.target_ssid
            if id not in devices:
                devices[id] = Device(id, last_seen_dts=capture_dts)
                log.debug("new device created: {}".format(devices[id]))
            if ssid:
                devices[id].add_ssid(ssid)
            if devices[id].last_seen_dts < capture_dts:
                devices[id].last_seen_dts = capture_dts
        return devices

    def _read_requests(self, load_dts):
        with open(self.request_filename) as file:
            raw = file.readlines()
        lines = [r.rstrip('\n') for r in raw if len(r) > 1]
        dump = '[' + ','.join(lines) + ']'
        all = _load_requests(dump)
        return [e for e in all if e.capture_dts < load_dts]


def _load_requests(dump):
    decoded = json.loads(dump)
    requests = []
    for d in decoded:
        try:
            capture_dts = _strptime(d['capture_dts'])
        except:
            capture_dts = None
        target_ssid = d['target_ssid']
        if target_ssid:
            target_ssid = repr(target_ssid)[2:-1]
        request = ProbeRequest(d['source_mac'], capture_dts,
                               target_ssid=target_ssid,
                               signal_strength=d['signal_strength'])
        requests.append(request)
    return requests


def _lookup_vendor(device_mac, session=requests.Session()):
    lookup_url = 'https://www.macvendorlookup.com/api/v2/' + device_mac
    try:
        vendor_response = session.get(lookup_url, timeout=20).json()[0]
    except Exception as e:
        log.error("Unable to lookup vendor.", e.msg)
        raise e
    else:
        return vendor_response


def set_vendors(devices, interval=1, max_slots=100):
    """Lookup the vendors for each device in a dict of devices.
    The lookup requests are executed in parallel for better performance when
    handling many devices.

    Keyword arguments:
    max_slots -- number of lookups which should be done in parallel
    interval -- seconds between checks if a lookup finished
    """

    class VendorLookupThread(Thread):
        """Helper class for concurrent vendor lookup."""

        def __init__(self, device, session):
            super(VendorLookupThread, self).__init__()
            self.device = device
            self.session = session

        def run(self):
            self.device.set_vendor(session)

    # the session is used to reuse https connections:
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=max_slots,
                                            pool_maxsize=max_slots,
                                            pool_block=True)
    session.mount('https://', adapter)
    # initialize one thread per device, but do not start them:
    threads = [VendorLookupThread(devices[id], session) for id in devices]
    slots = 0

    # start a number of threads and wait for some of them to finish before
    # starting more threads:
    for i in xrange(0, len(threads)):
        threads[i].start()
        slots += 1
        while slots >= max_slots:
            # wait before checking for free slots:
            sleep(interval)
            # check how many threads already finished:
            slots = sum([(1 if t.isAlive() else 0) for t in threads])
    # wait for remaining threads:
    while sum([(1 if t.isAlive() else 0) for t in threads]) > 0:
        sleep(interval)
    session.close()


def _strptime(s):
    """Parse datetime strings of the format 'YYYY-MM-DD hh:mm:ss.ssssss'.
    This is less flexible but more performant than datetime.datetime.strptime.
    """
    return datetime.datetime(year=int(s[:4]),
                             month=int(s[5:7]),
                             day=int(s[8:10]),
                             hour=int(s[11:13]),
                             minute=int(s[14:16]),
                             second=int(s[17:19]),
                             microsecond=int(s[20:26]))


def json_pretty(obj):
    """Generate pretty json string with indentions and spaces."""
    return json.dumps(obj.__jdict__(), indent=4, separators=(',', ': '))


def json_compact(obj):
    """Generate compact json string without whitespaces."""
    return json.dumps(obj.__jdict__(), separators=(',', ':'))
