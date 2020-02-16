#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 18:58:09 2020

copied from https://gist.github.com/yluthu/4f785d4546057b49b56c
https://gist.github.com/ninedraft/7c47282f8b53ac015c1e326fffb664b5
@author: emil
"""


import asyncio
import socket
from string import ascii_letters
import random
from typing import Tuple, Union, Text

Address = Tuple[str, int]

class BroadcastProtocol(asyncio.DatagramProtocol):

    def __init__(self, target: Address, *, loop: asyncio.AbstractEventLoop = None):
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
        string = ''.join([random.choice(ascii_letters) for _ in range(5)])
        print('sending:', string)
        self.transport.sendto(string.encode(), self.target)
        self.loop.call_later(5, self.broadcast)

loop = asyncio.get_event_loop()
coro = loop.create_datagram_endpoint(
    lambda: BroadcastProtocol(('192.168.1.255', 9000), loop=loop), local_addr=('0.0.0.0', 9000))
loop.run_until_complete(coro)
loop.run_forever()
loop.close()