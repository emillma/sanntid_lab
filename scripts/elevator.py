# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 12:07:36 2020

@author: user_id
"""
import asyncio


class elevator_handler:

    def __init__(self, port=15657):
        self.TCP_IP = 'localhost'
        self.TCP_PORT = port
        self.BUFFER_SIZE = 1024

        self.last_floor = None

    async def __aenter__(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.TCP_IP, self.TCP_PORT)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.writer.close()
        await self.writer.wait_closed()

    async def elev_tell(self, command):
        self.writer.write(command)
        await self.writer.drain()

    async def elev_get(self, command):
        await self.elev_tell(command)
        return await self.reader.read(4)

    async def go_up(self):
        com = bytearray.fromhex('01010000')
        await self.elev_tell(com)

    async def go_down(self):
        com = bytearray.fromhex('01ff0000')
        await self.elev_tell(com)

    async def set_floor_indicator(self, floor):
        com = bytearray.fromhex(f'03{floor:02x}0000')
        await self.elev_tell(com)

    async def stop(self):
        com = bytearray.fromhex('01000000')
        await self.elev_tell(com)

    async def get_stop_button(self):
        com = bytearray.fromhex('08000000')
        data = await self.elev_get(com)
        return data[1]

    async def get_floor(self):
        com = bytearray.fromhex('07000000')
        data = await self.elev_get(com)
        at_floor = data[1]
        floor = data[2]
        if not at_floor:
            return None
        else:
            return floor

    async def run(self):
        while 1:
            await self.go_down()
            while await self.get_floor() != 0:
                await asyncio.sleep(0.01)
            await self.go_up()
            while await self.get_floor() != 3:
                await asyncio.sleep(0.01)


async def main():
    eh1 = elevator_handler()
    async with eh1 as elev:
        task = asyncio.create_task(elev.run())
        await task
        # await elev.run()
        print('started stuff')

asyncio.run(main())
print('done')
