import datetime

from scapy.all import Dot11ProbeReq


def _extract_signal_strength(packet):
    try:
        extra = packet.notdecoded
        signal_strength = -(256 - ord(extra[-4:-3]))
    except Exception as e:
        print e
        signal_strength = None
    return signal_strength


def _extract_ssid(packet):
    ssid = packet.getlayer(Dot11ProbeReq).info
    if len(ssid) < 1:
        ssid = None
    return ssid


class ProbeRequest(object):

    def __init__(self, packet):
        self.capture_dts = datetime.datetime.now()
        self.target_mac = packet.addr3.lower()
        self.target_ssid = _extract_ssid(packet)
        self.source_mac = packet.addr2.lower()
        self.signal_strength = _extract_signal_strength(packet)

    def _get_id(self):
        return self.source_mac + str(self.capture_dts)

    def _get_type(self):
        return 'ProbeRequest'

    def __str__(self):
        return "Source: {} || SSID: {} || RSSi: {}".format(self.source_mac,
                                                           self.target_ssid,
                                                           self.signal_strength)


class Device(object):

    def __init__(self, request):
        self.device_mac = request.source_mac
        self.known_ssids = []
        self.last_seen_dts = datetime.datetime.now()

    def add_ssid(self, ssid):
        if ssid and ssid not in self.known_ssids:
            self.known_ssids.append(ssid)

    def _update_last_seen_dts(self):
        self.last_seen_dts = datetime.datetime.now()

    def _get_id(self):
        return self.device_mac

    def _get_type(self):
        return 'Device'

    def __str__(self):
        return "Device: {}".format(self.device_mac)


class Storage(object):

    def __init__(self, threshold=None):
        self.storage = {}
        if not threshold:
            threshold = datetime.timedelta(seconds=2)
        self.threshold = threshold

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
