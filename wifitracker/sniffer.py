import datetime
import logging

from scapy.all import sniff as scapy_sniff
from scapy.all import conf as scapy_conf
from scapy.all import Dot11, Dot11ProbeReq

from wifitracker.tracker import ProbeRequest, Tracker

TRACKER = None

log = logging.getLogger(__name__)

# constants for packet inspection:
PR_TYPE = 0
PR_SUBTYPE = 4


def _extract_rssi(packet):
    """Extract the RSSi (received signal strength indicator) from a wifi packet.
    """
    try:
        extra = packet.notdecoded
        signal_strength = -(256 - ord(extra[-4:-3]))
    except Exception as e:
        log.error("Unable to extract RSSi from captured packet.", e)
        signal_strength = None
    return signal_strength


def _extract_ssid(packet):
    """Extract the SSID (service set identifier) from a captured wifi packet.
    """
    try:
        ssid = str(packet.getlayer(Dot11ProbeReq).info)
        if len(ssid) < 1:
            ssid = None
    except Exception as e:
        # TODO: support for unicode?
        log.error("Unable to extract SSID from captured packet.", e)
        ssid = None
    return ssid


def packet_handler(packet):
    if packet.haslayer(Dot11):
        if (packet.type == PR_TYPE and packet.subtype == PR_SUBTYPE):
            request = summarize_probe_request(packet)
            log.info("captured probe request: {}".format(request))
            try:
                TRACKER.add_request(request)
            except Exception as e:
                log.error('Unable to add request', e)
            finally:
                TRACKER.release(request.source_mac)


def summarize_probe_request(packet):
    """Creates a ProbeRequest object from a 802.11 packet.
    """
    now = datetime.datetime.now()
    ssid = _extract_ssid(packet)
    rssi = _extract_rssi(packet)
    mac = packet.addr2.lower()
    return ProbeRequest(source_mac=mac, capture_dts=now,
                        target_ssid=ssid, signal_strength=rssi)


def sniff(interface):
    """Runs scapy.sniff() and calls a handler function (new thread) for each
    captured packet, matching the filter criteria.
    """
    global TRACKER
    TRACKER = Tracker('/var/opt/wifi-tracker')
    # The interface needs to be set explicitly due to a bug in scapy.
    # It is not sufficient to pass iface to the scniff function.
    scapy_conf.iface = interface
    # The filter only works on the assumption that only 802.11 packets are
    # received.
    # for more information on the filter, see man pages of tcpdump
    scapy_sniff(prn=packet_handler,
                filter='type mgt subtype probe-req',
                store=0)
