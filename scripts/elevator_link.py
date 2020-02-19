# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 12:07:36 2020

@author: user_id
"""
import asyncio


class ElevatorLink:

    def __init__(self, port=15657, floor_n=4):
        self.TCP_IP = 'localhost'
        self.TCP_PORT = port
        self.BUFFER_SIZE = 1024

        self.NUMBER_OF_FLOORS = floor_n
        self.last_floor = None
        self.reader_lock = asyncio.Lock()
        self.writer_lock = asyncio.Lock()
        self.every = 0.1

    async def __aenter__(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.TCP_IP, self.TCP_PORT)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.writer.close()
        await self.writer.wait_closed()

    async def elev_tell(self, command):
        async with self.writer_lock:
            self.writer.write(bytearray.fromhex(command))
            await self.writer.drain()

    async def elev_get(self, command):
        await self.elev_tell(command)
        async with self.reader_lock:
            return await self.reader.read(4)

    async def stop(self):
        await self.elev_tell('01000000')

    async def go_up(self):
        await self.elev_tell('01010000')

    async def go_down(self):
        await self.elev_tell('01ff0000')

    async def set_button_light(self, floor, button, value):
        await self.elev_tell(f'02{button:02x}{floor:02x}{value:02x}')

    async def set_floor_indicator(self, floor):
        await self.elev_tell(f'03{floor:02x}0000')

    async def set_door_light(self, value):
        await self.elev_tell(f'04{value:02x}0000')

    async def set_stop_light(self, value):
        await self.elev_tell(f'05{value:02x}0000')

    async def get_order_button(self, floor, button):
        return (await self.elev_get(f'06{button:02x}{floor:02x}00'))[1]

    async def get_floor(self):
        data = await self.elev_get('07000000')
        at_floor = data[1]
        floor = data[2]
        return floor if at_floor else None

    async def get_stop_button(self):
        return (await self.elev_get('08000000'))[1]

    async def get_obstruction_switch(self):
        return (await self.elev_get('09000000'))[1]

    @property
    def floor_n(self):
        return self.NUMBER_OF_FLOORS
