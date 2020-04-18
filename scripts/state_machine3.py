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
FLOORTIME = 4e6
TRAVELTIME = 2e6
UP = 0
DOWN = 1
DELIVER = 2
IDLE = 2

def time_to_floor(current, floor):
    return now() + abs(current - floor) * time_to_int(FLOORTIME)


class State:

    def __init__(self, parent: StateMachine):
        self.parent = parent

    async def enter(self):
        pass

    async def process(self):
        pass

    async def leave(self):
        pass

    def time_to_floor(self, floor):
        min_floor = min(self.floor, floor)
        max_floor = max(self.floor, floor)
        get = self.parent.common_ledger.get_selected_jobs(self.parent.id)
        deliver = self.parent.local_ledger.jobs
        stops = np.logical_or(get[:, self.parent.current_direction], deliver)
        stop_cout = np.count_nonzero(stops[min_floor + 1: max_floor])
        if stops[self.floor]:
            stop_cout += 1

        return (now()
                + (max_floor - min_floor) * TRAVELTIME
                + stop_cout * FLOORTIME)

    def update_select(self):
        get_jobs = self.parent.common_ledger.get_selected_jobs(self.parent.id)
        current_direction = self.parent.current_direction
        other_direction = UP if current_direction == DOWN else DOWN

        for floor in range(get_jobs.shape[0]):
            # self.parent.common_ledger.remove_selection(floor, other_direction,
            #                                            self.parent.id)
            if get_jobs[floor, current_direction]:
                self.parent.common_ledger.add_select(
                    floor, current_direction,
                    self.time_to_floor(floor),
                    self.parent.id)

    def clear_select(self):
        get_jobs = self.parent.common_ledger.get_selected_jobs(self.parent.id)
        for floor in range(get_jobs.shape[0]):
            self.parent.common_ledger.remove_selection(floor, UP,
                                                        self.parent.id)
            self.parent.common_ledger.remove_selection(floor, DOWN,
                                                        self.parent.id)

    async def clear_all_order_lights(self):
        for floor, order_type in product(range(NUMBER_OF_FLOORS), range(3)):
            await self.parent.elevator_link.set_button_light(
                floor, order_type, 0)

    @property
    def jobs(self):
        return self.parent.jobs

    @property
    def current_direction(self):
        return self.parent.current_direction

    @property
    def oldest_job(self):
        tmp = np.where(self.jobs, self.jobs, 2**63-1)
        return np.unravel_index(np.argmin(tmp, axis = None), tmp.shape)

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
                tmp = np.where(deliver_jobs, deliver_jobs, 2**64-1)
                oldest_deliver = np.argmin(tmp)

                if oldest_deliver >= self.floor:
                    self.parent.current_direction = UP
                else:
                    self.parent.current_direction = DOWN

                self.parent.idle_floor = oldest_deliver
                return AtFloor

            get_jobs = self.parent.common_ledger.available_jobs
            if np.any(get_jobs):

                tmp = np.where(get_jobs, get_jobs, 2**64-1)
                argmin = np.unravel_index(np.argmin(tmp), get_jobs.shape)
                oldest_get, old_direction = argmin
                self.parent.idle_floor = oldest_get
                if oldest_get > self.floor:
                    self.parent.current_direction = UP

                    for floor in range(self.floor, oldest_get):
                        self.parent.common_ledger.add_select(
                            floor, UP,
                            self.time_to_floor(floor),
                            self.parent.id)

                    self.parent.common_ledger.add_select(
                            oldest_get, old_direction,
                            self.time_to_floor(oldest_get),
                            self.parent.id)


                elif oldest_get < self.floor:
                    self.parent.current_direction = DOWN

                    for floor in range(self.floor, oldest_get, -1):

                        self.parent.common_ledger.add_select(
                            floor, DOWN,
                            self.time_to_floor(floor),
                            self.parent.id)

                    self.parent.common_ledger.add_select(
                            oldest_get, old_direction,
                            self.time_to_floor(oldest_get),
                            self.parent.id)


                else:
                     self.parent.current_direction = old_direction
                     self.parent.common_ledger.add_select(
                            oldest_get, old_direction,
                            self.time_to_floor(oldest_get),
                            self.parent.id)

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
        self.update_select()

    async def process(self):

        if np.any(self.jobs[(self.current_direction, DELIVER), self.floor]):
            return DoorOpen

        deliver_jobs = self.parent.local_ledger.jobs
        if np.any(deliver_jobs):

            if (np.any(np.argwhere(deliver_jobs) > self.floor)
                    and self.parent.current_direction == UP):

                return Up

            elif (np.any(np.argwhere(deliver_jobs) < self.floor)
                      and self.parent.current_direction == DOWN):

                return Down

        get_jobs = self.jobs[(UP, DOWN), :]

        if np.any(get_jobs):
            tmp = np.where(get_jobs, get_jobs, 2**64-1)
            argmin = np.unravel_index(np.argmin(tmp), get_jobs.shape)
            old_floor, old_direction = argmin

            if old_floor == self.floor:
                self.parent.current_direction = old_direction
                return DoorOpen

            elif self.parent.current_direction == UP:
                return Up

            elif self.parent.current_direction == DOWN:
                return Down

            # elif old_floor == self.floor:
            #     return DoorOpen
        return Idle

    async def leave(self):
        self.update_select()

    def open_door(self):
        deliver = self.parent.local_ledger.jobs[self.floor]

        let_on = self.parent.common_ledger.jobs[
                self.floor, self.parent.current_direction]

        return deliver or let_on


class DoorOpen(State):

    async def get_next_state(self):
        pass

    async def enter(self):
        await asyncio.sleep(0.5)
        await self.parent.elevator_link.set_door_light(1)
        retval, floor = await self.parent.elevator_link.get_floor()
        self.floor = floor

    async def process(self):

        while self.keep_door_open():
            await asyncio.sleep(1)
            self.parent.local_ledger.add_task_done(self.floor)

            self.parent.common_ledger.add_task_done(
                self.floor, self.parent.current_direction)


            if self.floor == self.parent.idle_floor:
                self.parent.common_ledger.add_task_done(
                    self.floor, self.parent.other_direction)

            await asyncio.sleep(1)

        return AtFloor

    async def leave(self):
        await self.parent.elevator_link.set_door_light(0)
        await asyncio.sleep(0.5)

    def keep_door_open(self):
        blocked = self.parent.local_ledger.block

        deliver = self.parent.local_ledger.jobs[self.floor]

        get = self.parent.common_ledger.jobs[
                self.floor, self.parent.current_direction]

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
        self.idle_floor = None
    async def run(self):
        while 1:
            logging.info(f'Entering \t\t {self.state}')
            await self.state.enter()

            logging.info(f'Processing \t {self.state}')
            state_generator = await self.state.process()

            logging.info(f'Leaving \t\t {self.state}\n')
            await self.state.leave()
            self.state = state_generator(self)

    @property
    def other_direction(self):
        return UP if self.current_direction == DOWN else DOWN

    @property
    def jobs(self):
        return np.hstack((self.common_ledger.get_selected_jobs(self.id),
                         self.local_ledger.jobs[:, None])).T
async def main():

    print('started')
    async with ElevatorLink() as elevator_link:
        logging.degub('got here')
        state_machine = StateMachine(elevator_link)
        await state_machine.run()
