import os
import queue
import random
import socket
import sys
from time import sleep

import webview
from scapy.all import rdpcap

from albibong.classes.logger import Logger
from albibong.classes.packet_handler import PacketHandler
from albibong.classes.utils import Utils
from albibong.threads.http_server import HttpServerThread
from albibong.threads.packet_handler_thread import PacketHandlerThread
from albibong.threads.sniffer_thread import SnifferThread
from albibong.threads.websocket_server import get_ws_server

logger = Logger(__name__, stdout=True, log_to_file=False)
PORT = random.randrange(8500, 8999)


def read_pcap(path):
    packet_handler = PacketHandler()
    scapy_cap = rdpcap(path)
    for packet in scapy_cap:
        packet_handler.handle(packet)


def sniff(useWebview, is_debug=False):

    _sentinel = object()
    packet_queue = queue.Queue()

    p = SnifferThread(
        name="sniffer", out_queue=packet_queue, sentinel=_sentinel, is_debug=is_debug
    )
    c = PacketHandlerThread(
        name="packet_handler",
        in_queue=packet_queue,
        sentinel=_sentinel,
    )

    p.start()
    c.start()

    ws_server = get_ws_server()
    ws_server.start()

    if useWebview:
        sock = socket.socket()
        sock.bind(("", 0))
        port = sock.getsockname()[1]
        sock.close()

        http_server = HttpServerThread(name="http_server", port=port)
        http_server.start()

        window = webview.create_window(
            "Albibong",
            url=f"http://localhost:{port}/",
            width=1280,
            height=720,
            zoomable=True,
        )

        def on_closing():
            c.stop()
            p.stop()
            ws_server.stop()
            http_server.stop()

        window.events.closing += on_closing

        webview.start()
    else:
        try:
            while True:
                sleep(100)
        except KeyboardInterrupt as e:
            p.stop()
            ws_server.stop()


def main(useWebview=True):
    if len(sys.argv) > 1:
        if sys.argv[-1] == "--debug":
            Utils.get_user_specifications("pip")
            sniff(useWebview, is_debug=True)
        else:
            ws_server = get_ws_server()
            ws_server.start()
            read_pcap(sys.argv[1])
    else:
        sniff(useWebview)
