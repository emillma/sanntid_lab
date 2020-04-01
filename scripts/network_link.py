#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 14:18:30 2020

@author: emil
"""


import udp as udp
import asyncio
import time
import logging
from typing import Optional

class NetworkLink:

    def __init__(self, port, common_ledger, queue_size=100, update_rate=1,
                 sendto = None):
        self.port = port
        self.queue_size = queue_size
        self.loop_time = 1/update_rate
        self.common_ledger = common_ledger
        self.id = hash(time.time())
        if sendto is None:
            self.sendto = [port]
        else:
            self.sendto = sendto

        self.endpoint = None
        # self.out_ip = '255.255.255.255'
        self.out_ip = 'localhost'
        self.out_addr = ('localhost', port)

    async def __aenter__(self):
        initial_port = self.port
        while 1:
            try:
                assert self.port <= initial_port + 5
                self.endpoint = await udp.open_endpoint(
                    port=self.port, queue_size=self.queue_size)
                return self
            except OSError:
                self.port += 1

    async def __aexit__(self, exc_type, exc, tb):
        self.endpoint.close()

    async def broadcast(self, data):
        for port in self.sendto:
            self.endpoint.send(data, (self.out_ip, port))


    def queie_is_empty(self):
        return self.endpoint.que_is_empty()

    async def pop(self):
        data, addr = await self.endpoint.receive()
        return data, addr

    async def run(self):
        while 1:
            start_time = time.time()
            while not self.endpoint.que_is_empty():
                data, addr = await self.pop()
                id_bytes = data[:8]
                json_data = data[8:]
                if int.from_bytes(id_bytes, 'big') != self.id:
                    self.common_ledger += json_data
            bytes_out = ((self.id).to_bytes(8, 'big')
                         + self.common_ledger.encode())
            await self.broadcast(bytes_out)

            delta = time.time() - start_time
            if self.loop_time < delta:
                logging.warning('Not enough time to finish')

            await asyncio.sleep(max(0, self.loop_time - delta))
