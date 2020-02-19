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

# common task
def create_task_get(floor, ud, timestamp):
    task_dict = {
        "floor": floor,
        "ud": ud,
        "timestamp": timestamp
    }
    return task_dict
    #dictionary floor, up, timestamp, retunrer

def create_done_get(floor, ud, timestamp):
    task_dict = {
        "floor": floor,
        "ud": ud,
        "timestamp": timestamp
    }
    return task_dict

def create_select(floor, type, timestamp, edt):
    print("Selected")

def create_deselect(floor, type, timestamp, id):
    print("Deselected")

# local task

def create_set_light_on(light_id, timestamp):
    print("Set light on")

def create_deselect(floor, type, timestamp, id):
    print("Deselected")

def create_set_light_on(light_id, timestamp):
    print("Set light on")

def create_set_light_off(light_id, timestamp):
    print("Set light off")

def create_stop(timestamp):
    print("Stop")

def create_blocked(timestamp):
    print("Blocked")

def create_deblocked(timestamp):
    print("Deblocked")

def create_task_deliver(floor, timestamp):
    print("Task deliver")

def create_done_deliver(floor, timestamp):
    print("Done deliver")

async def main():
    async with ElevatorLink() as el:
        while 1:
            await poll_buttons(el)
            await asyncio.sleep(0.1)

if __name__ == '__main__':
    asyncio.run(main())
