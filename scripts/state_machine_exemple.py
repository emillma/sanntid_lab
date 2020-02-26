# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 22:21:15 2020

@author: user_id
"""

from elevator_link import ElevatorLink
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)

class State:

    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        print(f'Entering {self}')

    async def process(self):
        pass

    async def leave(self):
        assert self.next_state


class InitState(State):

    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        await asyncio.sleep(1)

    async def process(self):
        self.next_state = StillState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state

class UpState(State):

    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        while await self.parent.elevator_link.go_up():
            await asyncio.sleep(0.1)

    async def process(self):
        while (await self.parent.elevator_link.get_floor())[1] != 3:
            await asyncio.sleep(0.1)
        self.next_state = StillState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state

class DownState(State):

    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        while await self.parent.elevator_link.go_down():
            await asyncio.sleep(0.1)

    async def process(self):
        while (await self.parent.elevator_link.get_floor())[1] != 0:
            await asyncio.sleep(0.1)
        self.next_state = StillState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state

class StillState(State):

    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        while await self.parent.elevator_link.stop():
            await asyncio.sleep(0.1)

    async def process(self):
        if (await self.parent.elevator_link.get_floor())[1] == 0:
            self.next_state = UpState(self.parent)
        elif (await self.parent.elevator_link.get_floor())[1] == 3:
            self.next_state = DownState(self.parent)
        else:
            self.next_state = UpState(self.parent)
        await asyncio.sleep(1)
    async def leave(self):
        assert self.next_state
        return self.next_state

class Statemachine:

    def __init__(self, elevator_link):
        self.elevator_link = elevator_link
        self.state = InitState(self)

    async def run(self):
        while 1:
            logging.info(f'Entering {self.state}')
            await self.state.enter()
            logging.info(f'Processing {self.state}')
            await self.state.process()
            logging.info(f'Leaving {self.state}')
            self.state = await self.state.leave()

async def main():
    async with ElevatorLink() as elevator_link:
        state_machine = Statemachine(elevator_link)
        await state_machine.run()

asyncio.run(main())