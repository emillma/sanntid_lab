from elevator_link import ElevatorLink
import asyncio
import logging
import time
from ledger_local import LocalLedger

logging.basicConfig(level=logging.DEBUG)

# NUMBER_OF_FLOORS = self.parent.elevator_link.floor_n()
NUMBER_OF_FLOORS = 4

orders = [2, None, 4, 8]


class State:

    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def clear_all_order_lights(self):
        for floor in range(0, NUMBER_OF_FLOORS):
            for order_type in range(0, 3):
                await self.parent.elevator_link.set_button_light(floor, order_type, 0)

    # async def stop_button_pressed(self):
    #    while await self.parent.elevator_link.get_stop_button():
    #        await self.parent.elevator_link.stop()
    #        await self.clear_all_order_lights()
    #    return

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
        await self.parent.elevator_link.set_door_light(0)
        await self.parent.clear_all_order_lights()
        await asyncio.sleep(1)

    async def process(self):
        while not (await self.parent.elevator_link.get_floor())[1]:
            await self.parent.elevator_link.go_down()
        self.next_state = AtFloorDoorClosedState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state


class BetweenFloorsNoDirectionState(State):
    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        await self.parent.clear_all_order_lights()
        await asyncio.sleep(1)

    async def process(self):
        if await self.parent.elevator_link.get_stop_button()[1]:
            await self.parent.elevator_link.set_stop_light(1)
            self.next_state = BetweenFloorsNoDirectionState(self.parent)
            await asyncio.sleep(0.1)

        if self.parent.last_direction == 0:
            self.next_state = UpState(self.parent)
        elif self.parent.last_direction == 1:
            self.next_state = DownState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state


class UpState(State):

    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        await self.parent.elevator_link.set_stop_light(0)
        self.parent.last_direction = 0
        self.parent.last_floor = (await self.parent.elevator_link.get_floor())[1]
        await self.parent.elevator_link.go_up()
        await asyncio.sleep(0.1)

    async def process(self):
        while not await self.parent.ledger_local.get_stop():  # While no stop signal
            try:
                for floor in range(self.parent.last_floor, NUMBER_OF_FLOORS):
                    assert not await self.parent.ledger_local.get_stop()
                    if (await self.parent.elevator_link.get_floor())[1] is floor:
                        self.parent.elevator_link.set_floor_indicator(floor)
                        if (await self.parent.deliver_tasks())[floor]:
                            self.next_state = AtFloorDoorOpenState(self.parent)
                    await asyncio.sleep(0.1)

            except AssertionError as e:
                self.parent.elevator_link.stop()
                self.parent.elevator_link.set_stop_light(1)
                if (await self.parent.elevator_link.get_floor())[1]:
                    self.next_state = AtFloorDoorOpenState(self.parent)
                else:
                    self.next_state = BetweenFloorsNoDirectionState(self.parent)

        while await self.parent.elevator_link.get_stop_button()[1] is not 1:
            for floor in range(self.parent.last_floor, NUMBER_OF_FLOORS):
                while (await self.parent.elevator_link.get_floor())[1] is None:
                    await asyncio.sleep(0.1)
                self.parent.last_floor = await self.parent.elevator_link.get_floor()[1]
                await self.parent.elevator_link.set_floor_indicator(self.parent.last_floor)
                for order_type in range(0, 3):
                    if await self.parent.elevator_link.get_order_button(floor, order_type):
                        if order_type == 0 or order_type == 2:
                            self.next_state = AtFloorDoorClosedState(self.parent)
                        else:
                            self.next_state = UpState(self.parent)
            # break
        if self.parent.elevator_link.get_stop_button()[1]:
            await self.parent.elevator_link.set_stop_light(1)

            if self.parent.elevator_link.get_floor()[1]:
                self.next_state = AtFloorDoorOpenState(self.parent)
            else:
                self.next_state = BetweenFloorsNoDirectionState(self.parent)


        # TODO await ?
            #  while (await self.parent.elevator_link.get_floor())[1] != 3:

        await asyncio.sleep(0.1)

    async def leave(self):
        await self.parent.elevator_link.set_button_light(self.parent.last_floor, 0, 0)  # Turn off up order light
        assert self.next_state
        return self.next_state


class DownState(State):

    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        await self.parent.elevator_link.set_stop_light(0)
        self.parent.last_direction = 1
        self.parent.last_floor = (await self.parent.elevator_link.get_floor())[1]
        await self.parent.elevator_link.go_down()
        await asyncio.sleep(0.1)

    async def process(self):
        while not await self.parent.ledger_local.get_stop():  # While no stop signal
            try:
                for floor in range(self.parent.last_floor, -1):  # Den skal gå til -1 og ikke 0 right?
                    assert not await self.parent.ledger_local.get_stop()
                    if (await self.parent.elevator_link.get_floor())[1] is floor:
                        self.parent.elevator_link.set_floor_indicator(floor)
                        if (await self.parent.deliver_tasks())[floor]:
                            self.next_state = AtFloorDoorOpenState(self.parent)
                    await asyncio.sleep(0.1)

            except AssertionError as e:
                self.parent.elevator_link.stop()
                self.parent.elevator_link.set_stop_light(1)
                if (await self.parent.elevator_link.get_floor())[1]:
                    self.next_state = AtFloorDoorOpenState(self.parent)
                else:
                    self.next_state = BetweenFloorsNoDirectionState(self.parent)

        # TODO something for when last floor is unknown
        else:
            for floor in range(self.parent.last_floor, -1):  # Iterate from current floor to the bottom

                while (await self.parent.elevator_link.get_floor())[1] is None:  # Waits while elevator is not at floor
                    await asyncio.sleep(0.1)
                self.parent.last_floor = self.parent.elevator_link.get_floor()[1]
                self.parent.elevator_link.set_floor_indicator(self.parent.last_floor)
                for order_type in range(0, 3):
                    if self.parent.elevator_link.get_order_button(floor, order_type):  # If orders
                        self.parent.elevator_link.set_button_light(floor, order_type, 1)
                        if order_type == 1 or order_type == 2:
                            self.next_state = AtFloorDoorClosedState(self.parent)
                        else:
                            self.next_state = DownState(self.parent)

            # TODO await asyncio.sleep(0.1)

    async def leave(self):
        # self.parent.elevator_link.set_button_light(self.parent.last_floor, 1, 0)  # Turn off down order light
        assert self.next_state
        return self.next_state


class AtFloorDoorClosedState(State):
    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        await self.parent.elevator_link.stop()
        await asyncio.sleep(0.1)
        self.parent.last_floor = (self.parent.elevator_link.get_floor())[1]
        await self.parent.elevator_link.set_floor_indicator(self.parent.last_floor)
        await asyncio.sleep(1)

    async def process(self):
        while not await self.parent.ledger_local.get_stop():
            try:
                assert not await self.parent.ledger_local.get_stop()
                await self.parent.elevator_link.set_stop_light(0)
                # TODO loop: take job, got job?
                # TODO Do job: find direction, go to state up or down

                # TODO Deliver tasks
                self.parent.deliver_tasks = await self.parent.ledger_local.get_deliver()
                if self.parent.last_direction is 0:  # 0 = up
                    for floor in range(self.parent.current_floor, len(self.parent.deliver_tasks)):
                        if await self.parent.deliver_tasks[floor]:
                            self.next_state = UpState(self.parent)
                elif self.parent.last_direction is 1:  # 1 = down
                    for floor in range(self.parent.current_floor, -1):
                        if await self.parent.deliver_tasks[floor]:
                            self.next_state = DownState(self.parent)
                elif self.parent.last_direction is None:
                    for floor in range(0, len(self.parent.deliver_tasks)):
                        if await self.parent.deliver_tasks[floor]:
                            self.next_state = UpState(self.parent)

                else:
                    self.next_state = AtFloorDoorClosedState(self.parent)

            except AssertionError as e:
                await self.parent.elevator_link.set_stop_light(1)
                self.next_state = AtFloorDoorOpenState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state


class AtFloorDoorOpenState(State):
    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        await self.parent.elevator_link.set_door_light(1)
        await asyncio.sleep(1)

    async def process(self):
        while not (await self.parent.ledger_local.get_stop() or await self.parent.ledger_local.get_block):
            try:
                for i_ in range(10):
                    assert not (await self.parent.ledger_local.get_stop() or await self.parent.ledger_local.get_block())
                    await self.parent.elevator_link.set_stop_light(0)
                    await self.parent.elevator_link.set_obstruction_light(0)
                    await asyncio.sleep(0.3)
                self.next_state = AtFloorDoorClosedState(self.parent)
            except AssertionError as e:
                if await self.parent.ledger_local.get_stop():
                    await self.parent.elevator_link.set_stop_light(1)
                if await self.parent.ledger_local.get_block():
                    await self.parent.elevator_link.set_obstruction_light(1)
                self.next_state = AtFloorDoorOpenState(self.parent)

    async def leave(self):
        await self.parent.elevator_link.set_door_light(0)
        assert self.next_state
        return self.next_state


class StateMachine:

    def __init__(self, elevator_link, local_ledger):
        self.elevator_link = elevator_link
        self.local_ledger = local_ledger
        self.state = InitState(self)
        self.last_floor = None
        self.next_floor = None
        self.last_direction = None
        self.deliver_tasks = []

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
        state_machine = StateMachine(elevator_link)
        await state_machine.run()

asyncio.run(main())
