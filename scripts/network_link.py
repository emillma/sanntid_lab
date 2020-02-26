#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 14:18:30 2020

@author: emil
"""


import udp as udp
import asyncio

class NetworkLink:

    def __init__(self, port, queue_size = 100):
        self.port = port
        self.endpoint = None
        self.queue_size = queue_size
        self.out_addr = ('255.255.255.255', port)

    async def __aenter__(self):
        self.endpoint = await udp.open_endpoint(
            port=self.port, queue_size=self.queue_size)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.endpoint.close()

    async def broadcast(self, data):
        self.endpoint.send(data, self.out_addr)

    def queie_is_empty(self):
        return self.endpoint.que_is_empty()

    async def pop(self):
        data, addr = await self.endpoint.receive()
        return data, addr


async def main():
    async with NetworkLink(9000) as nl:
        while 1:
            await nl.broadcast('hall2'.encode())
            while not nl.queie_is_empty():
                print(await nl.pop())
            await asyncio.sleep(1)

if __name__ == '__main__':
    asyncio.run(main())
