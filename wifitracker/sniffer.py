import logging

from scapy.all import sniff as scapy_sniff
from scapy.all import conf as scapy_conf
from scapy.all import Dot11

from wifitracker.tracker import ProbeRequest, Device
from wifitracker import STORAGE

log = logging.getLogger(__name__)

PR_TYPE = 0
PR_SUBTYPE = 4

DUMP_DIR = None


def packet_handler(packet):
    if packet.haslayer(Dot11):
        if (packet.type == PR_TYPE and packet.subtype == PR_SUBTYPE):
            request = ProbeRequest(packet)
            log.info("captured probe request: {}".format(request))
            store_probe_request(request)


def store_probe_request(request):
    # disabled to preserve memory until requests are actualle stored somewhere
    # STORAGE.add(request)
    try:
        device = STORAGE.get('Device', request.source_mac)
        device.update_last_seen_dts()
    except KeyError:
        device = Device(request)
        log.info("new device detected: {}".format(device))
    device.add_ssid(request.target_ssid)
    STORAGE.add(device)
    if DUMP_DIR:
        device.dump_json(DUMP_DIR)


def sniff(interface, dump_dir=None):
    global DUMP_DIR
    DUMP_DIR = dump_dir
    # The interface needs to be set explicitly due to a bug in scapy.
    # It is not sufficient to pass iface to the scniff function.
    scapy_conf.iface = interface
    # The filter only works on the assumption that only 802.11 packets are
    # received.
    # for more information on the filter, see man pages of tcpdump
    scapy_sniff(prn=packet_handler,
                filter='type mgt subtype probe-req',
                store=0)
