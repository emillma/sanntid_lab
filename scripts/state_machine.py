# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 13:08:26 2020

@author: user_id
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


def sort_best_jobs(jobs: np.array, current_floor: int) -> list([int, int]):
    """
    Sort the jobs.
    All jobs older than 10 secons are prioritized first by their timestamp,
    then they are prioritized after which one are clostest to the current floor
    and then by timestamp again.

    Parameters
    ----------
    jobs : np.array
        The UP DOWN jobs.
    current_floor : int
        The current floor.

    Returns
    -------
    list([int, int])
        List ist of the sorted jobs.

    """

    REALLY_OLD = 10e6
    FLOOR = 0
    DIR = 1
    tmp = np.where(jobs, jobs, 2**63-1)
    sort = np.array(np.unravel_index(np.argsort(tmp, axis=None), jobs.shape)).T

    removed_invalid = [i for i in sort if jobs[i[FLOOR], i[DIR]]]

    really_old = [i for i in removed_invalid
                  if now() - jobs[i[FLOOR], i[DIR]] > REALLY_OLD]

    really_old = sorted(really_old,
                        key=lambda job: jobs[job[FLOOR], job[DIR]])

    not_really_old = [i for i in removed_invalid
                      if now() - jobs[i[FLOOR], i[DIR]] <= REALLY_OLD]

    not_really_old = sorted(not_really_old,
                            key=lambda job: (abs(current_floor - job[FLOOR]),
                                             jobs[job[FLOOR], job[DIR]]))

    return really_old + not_really_old


def oldest(jobs: np.array) -> np.array or int:
    """
    Return the floor of the oldest request or the floor and direction if the
    job argument is a 2d array.

    Parameters
    ----------
    jobs : np.array
       The UP DOWN jobs, DELIVER jobs or UP DOWN DELIVER jobs.

    Returns
    -------
    np.array or int
        Floor or the oldes request or floor and direction.

    """

    tmp = np.where(jobs, jobs, 2**63-1)
    argmin = np.unravel_index(np.argmin(tmp), jobs.shape)
    return argmin if len(argmin) > 1 else argmin[0]


def in_between(start: int, stop: int) -> iter(int):
    """
    Returns an iterable of all the floor from start to stop.

    Parameters
    ----------
    start : int

    stop : int

    Returns
    -------
    iter(int)
    """

    if stop >= start:
        return range(start, stop)
    else:
        return range(start, stop, -1)


class State:
    """
    A generalization of the different States. All states inherits from this
    class.
    """

    def __init__(self, parent: StateMachine):
        """
        The parent is the Statemachine storing the shared information,
        reference to the local ledger, common ledger and network link etc.

        Parameters
        ----------
        parent : StateMachine
            The parent statemachine.
        """

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
        get_jobs = self.jobs[:, (UP, DOWN)]
        for floor in range(get_jobs.shape[1]):
            if get_jobs[self.current_direction, floor]:
                self.parent.common_ledger.add_select(
                    floor, self.current_direction,
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
        return np.unravel_index(np.argmin(tmp, axis=None), tmp.shape)

    def switch_direction(self):
        if self.current_direction == UP:
            self.parent.current_direction = DOWN
        else:
            self.parent.current_direction = UP


class Idle(State):

    async def enter(self):
        retval = await self.parent.elevator_link.stop()
        retval, floor = await self.parent.elevator_link.get_floor()
        self.floor = floor
        await self.parent.elevator_link.set_floor_indicator(floor)

    async def process(self):
        while True:
            deliver_jobs = self.jobs[:, DELIVER]

            if np.any(deliver_jobs):
                oldest_deliver = oldest(deliver_jobs)
                if oldest_deliver >= self.floor:
                    self.parent.current_direction = UP
                else:
                    self.parent.current_direction = DOWN

                return AtFloor

            jobs = self.parent.common_ledger.jobs
            for floor, direction in sort_best_jobs(jobs, self.floor):
                self.parent.common_ledger.add_select(
                        floor, self.current_direction,
                        self.time_to_floor(floor),
                        self.parent.id)

                if self.jobs[floor, direction]:
                    if floor > self.floor:
                        self.parent.current_direction = UP

                    elif floor < self.floor:
                        self.parent.current_direction = DOWN

                return AtFloor

            await asyncio.sleep(SLEEPTIME)

    async def leave(self):
        await asyncio.sleep(0.1)


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

        if self.current_direction == UP:
            if (not np.any(self.jobs[self.floor+1:, :])
                    and not self.jobs[self.floor, UP]):

                self.switch_direction()

        elif self.current_direction == DOWN:
            if (not np.any(self.jobs[:self.floor, :])
                    and not self.jobs[self.floor, DOWN]):

                self.switch_direction()

        if await self.open_door():
            return DoorOpen

        if not np.any(self.jobs):
            return Idle

        if self.current_direction == DOWN:
            return Down
        else:
            return Up

    async def open_door(self):
        await asyncio.sleep(0.2)
        pick_up = self.parent.common_ledger.jobs[
            self.floor, self.current_direction]
        return self.jobs[self.floor, DELIVER] or pick_up

    async def leave(self):
        self.update_select()


class DoorOpen(State):

    async def get_next_state(self):
        pass

    async def enter(self):
        retval, floor = await self.parent.elevator_link.get_floor()
        self.floor = floor

    async def process(self):
        while True:
            await self.parent.elevator_link.set_door_light(1)
            self.parent.local_ledger.add_task_done(self.floor)

            self.parent.common_ledger.add_task_done(
                self.floor, self.parent.current_direction)

            await asyncio.sleep(2)
            if not self.keep_door_open():
                break

        return AtFloor

    async def leave(self):
        await self.parent.elevator_link.set_door_light(0)
        await asyncio.sleep(0.5)

    def keep_door_open(self):
        blocked = self.parent.local_ledger.block

        deliver = self.jobs[self.floor, DELIVER]

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
    def __init__(self, elevator_link: ElevatorLink,
                 local_ledger: LocalLedger,
                 common_ledger: CommonLedger,
                 id=None):

        if id is None:
            self.id = hash(now())
        else:
            self.id = id

        self.elevator_link = elevator_link
        self.local_ledger = local_ledger
        self.common_ledger = common_ledger
        self.state = Init(self)
        self.current_direction = None
        self.idle_floor = None

    async def run(self):
        while 1:
            logging.info(f'Entering \t {type(self.state)}, {self.id}')
            await self.state.enter()

            logging.info(f'Processing \t {type(self.state)}, {self.id}')
            state_generator = await self.state.process()

            logging.info(f'Leaving \t {type(self.state)}, {self.id}\n')
            await self.state.leave()
            self.state = state_generator(self)

    @property
    def other_direction(self):
        return UP if self.current_direction == DOWN else DOWN

    @property
    def jobs(self):
        return np.hstack((self.common_ledger.get_selected_jobs(self.id),
                         self.local_ledger.jobs[:, None]))


async def main():

    print('started')
    async with ElevatorLink() as elevator_link:
        logging.degub('got here')
        state_machine = StateMachine(elevator_link)
        await state_machine.run()
