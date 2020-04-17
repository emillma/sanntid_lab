# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 16:34:22 2020

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


class State:

    def __init__(self, parent: StateMachine, previous_state):
        self.parent = parent
        self.previous_state = previous_state

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


class Init(State):

    def __init__(self, parent: StateMachine):
        super().__init__(parent)

    async def enter(self):
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
                    return AtFloorDown
                await asyncio.sleep(SLEEPTIME)
        else:
            return AtFloorDown

    async def leave(self):
        pass


class Idle(State):

        async def process(self):
            deliver = self.parent.local_ledger.deliver
            for floor, direction in product(range(NUMBER_OF_FLOORS), [1, 2]):
                self.parent.common_ledger.add_select(
                    floor, direction, self.parent.id,
                    now() + abs(self.floor - floor) * time_to_int(FLOORTIME))

            selected_jobs = self.parent.common_ledger.get_selected_jobs(
                self.parent.id)

            if np.any(deliver or np.any(selected_jobs)):
                  return AtFloorDown

            asyncio.sleep(SLEEPTIME)

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
                return self.next_state()
            await asyncio.sleep(SLEEPTIME)


class Down(Travel):
    async def set_direction(self):
        return await self.parent.elevator_link.go_down()

    def next_state(self):
        return AtFloorDown


class Up(Travel):
    async def set_direction(self):
        return await self.parent.elevator_link.go_up()

    def next_state(self):
        return AtFloorUp


class AtFloor(State):

    def __init__(self, parent: StateMachine):
        super().__init__(parent)
        self.diraction = None
        self.open_state = None

    async def get_next_state(self, tasks):
        pass

    async def enter(self):
        retval = await self.parent.elevator_link.stop()
        retval, floor = await self.parent.elevator_link.get_floor()
        self.floor = floor
        retval = await self.parent.elevator_link.set_floor_indicator(floor)

    async def process(self):
        while True:
            deliver_jobs = self.parent.local_ledger.deliver
            get_jobs = self.parent.common_ledger.available_jobs

            if deliver_jobs[self.floor] or get_jobs[self.floor, self.direction]:
                return self.open_state

            deliver_floors = np.argwhere(deliver_jobs).ravel()
            for floor in self.nextfloors():

                self.parent.common_ledger.add_select(
                    floor, self.direction, self.parent.id,
                    now() + abs(self.floor - floor) * time_to_int(FLOORTIME))

            get_floors = np.argwhere(
                self.parent.common_ledger.get_selected_jobs(self.parent.id))
            get_floors = get_floors[:, self.diraction].ravel()

            tasks = np.append(deliver_floors, get_floors)

            return await self.get_next_state(tasks)

    async def leave(self):
        pass

class AtFloorIdle(AtFloor):
    def __init__(self):
        pass

class AtFloorDown(AtFloor):
    def __init__(self, parent: StateMachine):
        super().__init__(parent)
        self.direction = 1
        self.open_state = DoorOpenDown

    def nextfloors(self):
        return range(self.floor)

    async def get_next_state(self, tasks):
        any_below = (np.any(tasks < self.floor))
        if any_below:
            return Down
        else:
            await asyncio.sleep(SLEEPTIME)
            return AtFloorUp


class AtFloorUp(AtFloor):
    def __init__(self, parent: StateMachine):
        super().__init__(parent)
        self.direction = 0
        self.open_state = DoorOpenUp

    def nextfloors(self):
        return range(self.floor + 1, NUMBER_OF_FLOORS)

    async def get_next_state(self, tasks):
        any_above = (np.any(tasks > self.floor))
        if any_above:
            return Up
        else:
            await asyncio.sleep(SLEEPTIME)
            return AtFloorDown


class DoorOpen(State):

    async def get_next_state(self):
        pass

    async def enter(self):
        await asyncio.sleep(1)
        await self.parent.elevator_link.set_door_light(1)
        retval, floor = await self.parent.elevator_link.get_floor()
        self.current_floor = floor

    async def process(self):

        while (self.parent.local_ledger.block
                or self.parent.local_ledger.deliver[self.current_floor]
                or self.parent.common_ledger.available_jobs[
                    self.current_floor, self.direction]):
            await asyncio.sleep(1)
            self.parent.local_ledger.add_task_done(self.current_floor)
            self.parent.common_ledger.add_task_done(self.current_floor,
                                                    self.direction)
            await asyncio.sleep(1)

        return await self.get_next_state()

    async def leave(self):
        await self.parent.elevator_link.set_door_light(0)
        await asyncio.sleep(1)


class DoorOpenUp(DoorOpen):
    def __init__(self, parent: StateMachine):
        super().__init__(parent)
        self.direction = 0

    async def get_next_state(self):
        return AtFloorUp


class DoorOpenDown(DoorOpen):
    def __init__(self, parent: StateMachine):
        super().__init__(parent)
        self.direction = 1

    async def get_next_state(self):
        return AtFloorDown


class StateMachine:
    def __init__(self, elevator_link: ElevatorLink, local_ledger: LocalLedger,
                 common_ledger: CommonLedger):
        self.id = hash(now())
        self.elevator_link = elevator_link
        self.local_ledger = local_ledger
        self.common_ledger = common_ledger
        self.state = Init(self)

    async def run(self):
        while 1:
            logging.info(f'Entering {self.state}')
            await self.state.enter()

            logging.info(f'Processing {self.state}')
            state_generator = await self.state.process()

            logging.info(f'Leaving {self.state}')
            await self.state.leave()
            self.state = state_generator(self)

async def main():

    print('started')
    async with ElevatorLink() as elevator_link:
        logging.degub('got here')
        state_machine = StateMachine(elevator_link)
        await state_machine.run()

# if __name__ == '__main__':
#     import nest_asyncio
#     nest_asyncio.apply()
#     asyncio.run(main())
