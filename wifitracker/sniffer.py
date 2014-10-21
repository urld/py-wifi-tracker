import logging

from scapy.all import Dot11, Dot11ProbeReq
from scapy.all import sniff as scapysniff

log = logging.getLogger(__name__)

PR_TYPE = 0
PR_SUBTYPE = 4


def _extract_signal_strength(packet):
    try:
        extra = packet.notdecoded
        signal_strength = -(256 - ord(extra[-4:-3]))
    except Exception as e:
        print e
        signal_strength = None
    return signal_strength


class ProbeRequest(object):

    def __init__(self, packet):
        self.target = packet.addr3
        self.source = packet.addr2
        self.signal_strength = _extract_signal_strength(packet)
        self.source_ssid = None
        ssid = packet.getlayer(Dot11ProbeReq).info
        if len(ssid) > 0:
            self.source_ssid = ssid

    def __str__(self):
        return "Source: {} || SSID: {} || RSSi: {}".format(self.source,
                                                           self.target_ssid,
                                                           self.signal_strength)


def packet_handler(packet):
    if packet.haslayer(Dot11):
        if (packet.type == PR_TYPE and packet.subtype == PR_SUBTYPE):
            request = ProbeRequest(packet)
            log.info(request)


def sniff(iface):
    scapysniff(iface=iface, prn=packet_handler)
