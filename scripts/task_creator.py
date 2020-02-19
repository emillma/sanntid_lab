#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 16:55:19 2020

@author: emil


Husk a starte heissim før du kjører.

"""

from elevator_link import ElevatorLink
import itertools
import numpy as np
import asyncio

async def poll_buttons(elevator_link):
        order_buttons = np.zeros((elevator_link.floor_n, 3), dtype=np.bool)
        stop_button = False
        obstruction = False
        for floor, order in itertools.product(range(elevator_link.floor_n),
                                              range(3)):
            # Order: Up: 0, Down: 1, Cab: 2
            if (floor == 0 and order == 1
                    or floor == elevator_link.floor_n - 1 and order == 0):
                continue  # No point in polling invalid buttons

            order_buttons[floor, order] = await elevator_link.get_order_button(
                floor, order)
        stop_button = await elevator_link.get_stop_button()
        obstruction = await elevator_link.get_obstruction_switch()

        if np.any(order_buttons) or stop_button or obstruction:
            print(order_buttons)


async def main():
    async with ElevatorLink() as el:
        while 1:
            await poll_buttons(el)
            await asyncio.sleep(0.1)

if __name__ == '__main__':
    asyncio.run(main())
