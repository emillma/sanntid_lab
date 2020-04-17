# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 13:08:26 2020

@author: emilm
"""


from __future__ import annotations
from elevator_link import ElevatorLink
import asyncio
import logging
from ledger_local import LocalLedger
from ledger_common import CommonLedger
from itertools import product
from utils import now, time_to_int
import numpy as np


NUMBER_OF_FLOORS = 4
SLEEPTIME = 0.02
FLOORTIME = 2
UP = 0
DOWN = 1
IDLE = 2

def time_to_floor(current, floor):
    return now() + abs(current - floor) * time_to_int(FLOORTIME)


class State:

    def __init__(self, parent: StateMachine):
        self.parent = parent

    async def enter(self):
        print(f'Entering {self}')

    async def process(self):
        pass

    async def leave(self):
        pass

    async def clear_all_order_lights(self):
        for floor, order_type in product(range(NUMBER_OF_FLOORS), range(3)):
            await self.parent.elevator_link.set_button_light(
                floor, order_type, 0)


class Idle(State):

    async def enter(self):
        retval = await self.parent.elevator_link.stop()
        retval, floor = await self.parent.elevator_link.get_floor()
        self.floor = floor
        await self.parent.elevator_link.set_floor_indicator(floor)

    async def process(self):
        while True:
            deliver_jobs = self.parent.local_ledger.jobs
            if np.any(deliver_jobs):
                if np.argmax(deliver_jobs) >= self.floor:
                    self.parent.current_direction = UP
                else:
                    self.parent.current_direction = DOWN
                return AtFloor

            get_jobs = self.parent.common_ledger.available_jobs
            if np.any(get_jobs):

                max_arg = np.unravel_index(np.argmax(get_jobs), get_jobs.shape)
                max_floor, max_direction = max_arg
                if max_floor > self.floor:

                    for floor in range(self.floor, max_floor):
                        self.parent.common_ledger.add_select(
                            floor, UP,
                            time_to_floor(self.floor, floor),
                            self.parent.id)

                    self.parent.common_ledger.add_select(
                            max_floor, max_direction,
                            time_to_floor(self.floor, max_floor),
                            self.parent.id)

                    self.parent.current_direction = UP

                elif max_floor < self.floor:

                    for floor in range(max_floor + 1, self.floor + 1):
                        self.parent.common_ledger.add_select(
                            floor, UP,
                            time_to_floor(self.floor, floor),
                            self.parent.id)

                    self.parent.common_ledger.add_select(
                            max_floor, max_direction,
                            time_to_floor(self.floor, max_floor),
                            self.parent.id)

                    self.parent.current_direction = DOWN

                else:
                     self.parent.common_ledger.add_select(
                            max_floor, max_direction,
                            time_to_floor(self.floor, max_floor),
                            self.parent.id)
                     self.parent.current_direction = max_direction

                return AtFloor

            await asyncio.sleep(SLEEPTIME)


class Init(State):

    def __init__(self, parent: StateMachine):
        super().__init__(parent)

    async def enter(self):
        self.parent.current_direction = DOWN
        pass

    async def process(self):
        retval, floor = await self.parent.elevator_link.get_floor()
        assert retval is None
        if floor is None:
            while True:
                await self.parent.elevator_link.go_down()
                retval, floor = await self.parent.elevator_link.get_floor()
                assert retval is None
                if floor is not None:
                    return AtFloor
                await asyncio.sleep(SLEEPTIME)
        else:
            return AtFloor

    async def leave(self):
        pass


class AtFloor(State):

    async def enter(self):
        retval = await self.parent.elevator_link.stop()
        retval, floor = await self.parent.elevator_link.get_floor()
        self.floor = floor
        await self.parent.elevator_link.set_floor_indicator(floor)

    async def process(self):

        if self.open_door():
            return DoorOpen

        deliver_jobs = self.parent.local_ledger.jobs
        if np.any(deliver_jobs):
            if np.argmax(deliver_jobs) >= self.floor:
                return Up
            else:
                return Down

        get_jobs = self.parent.common_ledger.get_selected_jobs(
            self.parent.id)

        if np.any(get_jobs):
            max_arg = np.unravel_index(np.argmax(get_jobs), get_jobs.shape)
            max_floor, max_direction = max_arg
            if max_floor > self.floor:
                return Up
            elif max_floor < self.floor:
                return Down

            elif max_floor == self.floor:
                self.parent.current_direction = max_direction

        return Idle

    def open_door(self):
        deliver = self.parent.local_ledger.jobs[self.floor]

        let_on = self.parent.common_ledger.jobs[
                self.floor, self.parent.current_direction]

        return deliver or let_on


class DoorOpen(State):

    async def get_next_state(self):
        pass

    async def enter(self):
        await asyncio.sleep(1)
        await self.parent.elevator_link.set_door_light(1)
        retval, floor = await self.parent.elevator_link.get_floor()
        self.current_floor = floor

    async def process(self):

        while self.keep_door_open():
            await asyncio.sleep(1)
            self.parent.local_ledger.add_task_done(self.current_floor)

            self.parent.common_ledger.add_task_done(
                self.current_floor, self.parent.current_direction)

            await asyncio.sleep(1)

        return AtFloor

    async def leave(self):
        await self.parent.elevator_link.set_door_light(0)
        await asyncio.sleep(1)

    def keep_door_open(self):
        blocked = self.parent.local_ledger.block

        deliver = self.parent.local_ledger.jobs[self.current_floor]

        get = self.parent.common_ledger.jobs[
                self.current_floor, self.parent.current_direction]

        return blocked or deliver or get


class Travel(State):

    async def set_direction(self):
        pass

    def next_state(self):
        pass

    async def enter(self):
        retval = await self.set_direction()
        assert retval is None
        retval, floor = await self.parent.elevator_link.get_floor()
        self.last_floor = floor

    async def process(self):
        while True:
            retval, floor = await self.parent.elevator_link.get_floor()
            assert retval is None
            if floor is not None and floor != self.last_floor:
                return AtFloor
            await asyncio.sleep(SLEEPTIME)


class Down(Travel):
    async def set_direction(self):
        self.parent.current_direction = DOWN
        return await self.parent.elevator_link.go_down()


class Up(Travel):
    async def set_direction(self):
        self.parent.current_direction = UP
        return await self.parent.elevator_link.go_up()


class StateMachine:
    def __init__(self, elevator_link: ElevatorLink, local_ledger: LocalLedger,
                 common_ledger: CommonLedger):
        self.id = hash(now())
        self.elevator_link = elevator_link
        self.local_ledger = local_ledger
        self.common_ledger = common_ledger
        self.state = Init(self)
        self.current_direction = None

    async def run(self):
        while 1:
            logging.info(f'Entering \t\t {self.state}')
            await self.state.enter()

            logging.info(f'Processing \t {self.state}')
            state_generator = await self.state.process()

            logging.info(f'Leaving \t\t {self.state}\n')
            await self.state.leave()
            self.state = state_generator(self)


async def main():

    print('started')
    async with ElevatorLink() as elevator_link:
        logging.degub('got here')
        state_machine = StateMachine(elevator_link)
        await state_machine.run()
