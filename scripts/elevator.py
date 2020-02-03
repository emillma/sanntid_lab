# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 12:07:36 2020

@author: user_id
"""
import asyncio
import numpy as np
import itertools

class elevator_handler:

    def __init__(self, port=15657, floor_n=4):
        self.TCP_IP = 'localhost'
        self.TCP_PORT = port
        self.BUFFER_SIZE = 1024

        self.floor_n = floor_n
        self.last_floor = None
        self.reader_lock = asyncio.Lock()

    async def __aenter__(self):
        self.reader, self.writer = await asyncio.open_connection(
            self.TCP_IP, self.TCP_PORT)
        return self

    async def __aexit__(self, exc_type, exc, tb):
        self.writer.close()
        await self.writer.wait_closed()

    async def elev_tell(self, command):
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

    async def get_order_button(self, floor, button):
        return (await self.elev_get(f'06{button:02x}{floor:02x}00'))[1]

    async def get_floor(self):
        data = await self.elev_get('07000000')
        at_floor = data[1]
        floor = data[2]
        if not at_floor:
            return None
        else:
            return floor

    async def get_stop_button(self):
        return (await self.elev_get('08000000'))[1]

    async def get_obstruction_switch(self):
        return (await self.elev_get('09000000'))[1]

    async def set_floor_indicator(self, floor):
        await self.elev_tell(f'03{floor:02x}0000')

    async def poll_buttons(self):
        while 1:
            await asyncio.sleep(0.1)
            order_buttons = np.zeros((self.floor_n, 3), dtype=np.bool)
            stop_button = False
            obstruction = False
            for floor, order in itertools.product(range(self.floor_n),
                                                  range(3)):
                # Order: Up: 0, Down: 1, Cab: 2
                if (floor == 0 and order == 1
                        or floor == self.floor_n - 1 and order == 0):
                    continue  # No point in polling invalid buttons

                order_buttons[floor, order] = await self.get_order_button(
                    floor, order)
            stop_button = await self.get_stop_button()
            obstruction = await self.get_obstruction_switch()

            if np.any(order_buttons) or stop_button or obstruction:
                print(order_buttons)

    async def go_up_down(self):
        while 1:
            await self.go_down()
            while await self.get_floor() != 0:
                await asyncio.sleep(0.1)
            await self.go_up()
            while await self.get_floor() != 3:
                await asyncio.sleep(0.1)


async def main():
    eh1 = elevator_handler()
    async with eh1 as elev:
        std = asyncio.gather(elev.go_up_down(), elev.poll_buttons())
        # std = asyncio.create_task(elev.poll_buttons())
        await std
        # await elev.run()
        print('started stuff')

asyncio.run(main())
print('done')
