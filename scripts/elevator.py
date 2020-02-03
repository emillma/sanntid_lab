# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 12:07:36 2020

@author: user_id
"""
import socket
import asyncio

class elevator_handler:

    def __init__(self, port=15657):
        self.TCP_IP = 'localhost'
        self.TCP_PORT = port
        self.BUFFER_SIZE = 1024

    async def __aenter__(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.TCP_IP, self.TCP_PORT)
        return self

    async def elev_tell(self, command):
        self.writer.write(command)
        await self.writer.drain()

    async def go_up(self):
        com = bytearray.fromhex('01010000')
        await self.elev_tell(com)

    async def go_down(self):
        com = bytearray.fromhex('01ff0000')
        await self.elev_tell(com)

    async def stop(self):
        com = bytearray.fromhex('01000000')
        await self.elev_tell(com)

    async def __aexit__(self, exc_type, exc, tb):
        self.writer.close()
        await self.writer.wait_closed()


async def main():
    eh1 = elevator_handler()
    async with eh1 as elev:
        await elev.go_down()


asyncio.run(main())
print('done')
