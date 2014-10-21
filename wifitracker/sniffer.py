import logging

from scapy.all import sniff as scapysniff
from scapy.all import Dot11

from wifitracker.tracker import ProbeRequest, Device
from wifitracker import STORAGE

log = logging.getLogger(__name__)

PR_TYPE = 0
PR_SUBTYPE = 4


def packet_handler(packet):
    if packet.haslayer(Dot11):
        if (packet.type == PR_TYPE and packet.subtype == PR_SUBTYPE):
            request = ProbeRequest(packet)
            log.debug(request)
            store_probe_request(request)


def store_probe_request(request):
    STORAGE.add(request)
    try:
        device = STORAGE.get('Device', request.source_mac)
    except KeyError:
        device = Device(request)
        log.info("New device detected: {}".format(device))
    device.add_ssid(request.target_ssid)
    STORAGE.add(device)


def sniff(iface):
    scapysniff(iface=iface, prn=packet_handler)
