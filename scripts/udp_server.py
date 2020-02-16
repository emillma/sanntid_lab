#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Feb 16 14:52:54 2020

@author: emil
"""


import asyncio
import socket
from string import ascii_letters
import random
from typing import Tuple, Union, Text

Address = Tuple[str, int]

key = ''.join([random.choice(ascii_letters) for _ in range(5)]) + '_'

class BroadcastProtocol(asyncio.DatagramProtocol):

    def __init__(self, target: Address, *,
                 loop: asyncio.AbstractEventLoop = None):
        super().__init__()
        self.target = target
        self.loop = asyncio.get_event_loop() if loop is None else loop

    def connection_made(self, transport: asyncio.transports.DatagramTransport):
        print('started')
        self.transport = transport
        sock = transport.get_extra_info("socket")  # type: socket.socket
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.broadcast()

    def datagram_received(self, data: Union[bytes, Text], addr: Address):
        print('data received:', data, addr)

    def broadcast(self):
        string = ''.join([random.choice(ascii_letters) for _ in range(random.randint(1,10))])
        string = key + string
        print('sending:', string)
        self.transport.sendto(string.encode(), self.target)
        self.loop.call_later(1, self.broadcast)


loop = asyncio.get_event_loop()
coro = loop.create_datagram_endpoint(
    lambda: BroadcastProtocol(('255.255.255.255', 9000)),
    local_addr=('10.24.32.193', 9000), allow_broadcast=True)


loop.run_until_complete(coro)
loop.run_forever()
loop.close()
