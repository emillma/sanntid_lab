#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 16:49:26 2020

@author: emil
"""


import asyncio


class DiscoveryProtocol(asyncio.DatagramProtocol):

    def __init__(self):
        super().__init__()

    def connection_made(self, transport):
        self.transport = transport

    def datagram_received(self, data, addr):
        print(data, addr)


def start_discovery():
    loop = asyncio.get_event_loop()
    t = loop.create_datagram_endpoint(lambda: DiscoveryProtocol(), local_addr=('0.0.0.0',9000))
    loop.run_until_complete(t)
    loop.run_forever()

start_discovery()