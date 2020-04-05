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
from utils import now
import numpy as np
NUMBER_OF_FLOORS = 4
SLEEPTIME = 0.02

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


class InitState(State):

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
                    return AtFloorDoorClosedState
                await asyncio.sleep(SLEEPTIME)
        else:
            return AtFloorDoorClosedState

    async def leave(self):
        pass


class UpState(State):

    def __init__(self, parent: StateMachine):
        super().__init__(parent)

    async def enter(self):
        retval = await self.parent.elevator_link.go_up()
        assert retval is None
        self.parent.last_direction = UpState

    async def process(self):
        while True:
            retval, floor = await self.parent.elevator_link.get_floor()
            # assert retval is None
            if floor is not None and floor != self.parent.last_floor:
                return AtFloorDoorClosedState
            await asyncio.sleep(SLEEPTIME)


class DownState(State):

    def __init__(self, parent: StateMachine):
        super().__init__(parent)

    async def enter(self):
        retval = await self.parent.elevator_link.go_down()
        assert retval is None
        self.parent.last_direction = DownState

    async def process(self):
        while True:
            retval, floor = await self.parent.elevator_link.get_floor()
            assert retval is None
            if floor is not None and floor != self.parent.last_floor:
                return AtFloorDoorClosedState
            await asyncio.sleep(SLEEPTIME)


class AtFloorDoorClosedState(State):

    def __init__(self, parent: StateMachine):
        super().__init__(parent)

    async def enter(self):
        retval = await self.parent.elevator_link.stop()
        retval, floor = await self.parent.elevator_link.get_floor()
        self.parent.current_floor = floor
        await self.parent.elevator_link.set_floor_indicator(floor)
        assert retval is None

    async def process(self):
        while True:
            if self.parent.local_ledger.get_deliver()[
                    self.parent.current_floor]:

                return AtFloorDoorOpenState

            deliver_floors = np.argwhere(
                    self.parent.local_ledger.get_deliver()).ravel()
            if len(deliver_floors) != 0:
                any_above = np.any(deliver_floors > self.parent.current_floor)
                any_below = np.any(deliver_floors < self.parent.current_floor)
                if any_above and any_below:
                    return self.last_direction
                elif any_above:
                    return UpState
                elif any_below:
                    return DownState

            await asyncio.sleep(SLEEPTIME)

    async def leave(self):
        self.parent.last_floor = self.parent.current_floor

class AtFloorDoorOpenState(State):

    def __init__(self, parent: StateMachine):
        super().__init__(parent)

    async def enter(self):
        await asyncio.sleep(1)
        await self.parent.elevator_link.set_door_light(1)

    async def process(self):
        current_floor = self.parent.current_floor

        while (self.parent.local_ledger.get_block()
                or self.parent.local_ledger.get_deliver()[current_floor]):
            await asyncio.sleep(1)
            self.parent.local_ledger.add_task_done(self.parent.current_floor)
            await asyncio.sleep(1)

        return AtFloorDoorClosedState

    async def leave(self):
        await self.parent.elevator_link.set_door_light(0)
        await asyncio.sleep(1)


class StateMachine:
    def __init__(self, elevator_link: ElevatorLink, local_ledger: LocalLedger,
                 common_ledger: CommonLedger):
        self.elevator_link = elevator_link
        self.local_ledger = local_ledger
        self.common_ledger = common_ledger
        self.state = InitState(self)

        self.last_floor = None
        self.current_floor = None
        self.next_floor = None

        self.last_direction = DownState
        self.current_direction = None
        self.next_direction = None
        self.deliver_tasks = []

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
