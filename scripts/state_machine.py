from elevator_link import ElevatorLink
import asyncio
import numpy as np
import logging
logging.basicConfig(level=logging.DEBUG)

# NUMBER_OF_FLOORS = self.parent.elevator_link.floor_n()
NUMBER_OF_FLOORS = 4

orders = np.zeros[NUMBER_OF_FLOORS]


def elevator_at_new_floor():
    # TODO
    return 1


def stop_at_floor():
    # TODO
    return 1


def open_door():
    # TODO
    return 0


def go_to_new_floor():
    # TODO
    return 1

# Gets list with length = NUM_OF_FLOORS, one integer per floor representing time order received, None for no order. Priority = smallest integer = oldest order

orders = zeros


class State:

    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    def clear_all_order_lights(self):
        for floor in range (0, NUMBER_OF_FLOORS):
            for order_type in range (0,3):
                self.parent.elevator_link.set_button_light(floor, order_type, 0)

    async def stop_button_pressed(self):
        while await self.parent.elevator_link.get_stop_button():
            self.parent.elevator_link.stop()
            self.clear_all_order_lights()
        return

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
        self.next_state = BetweenFloorsNoDirectionState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state


class BetweenFloorsNoDirectionState(State):
    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        await asyncio.sleep(1)

    async def process(self):
        if self.parent.elevator_link.get_stop_button():
            self.parent.elevator_link.set_stop_light(1)
            self.next_state = BetweenFloorsNoDirectionState(self.parent)
        else:
            self.next_state = TransitState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state


class TransitState(State):
    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        self.parent.elevator_link.set_stop_light(0)
        await asyncio.sleep(1)

    async def process(self):
        if self.parent.elevator_link.get_stop_button():
            self.parent.elevator_link.set_stop_light(1)

            if self.parent.elevator_link.get_floor():
                self.next_state = AtFloorDoorOpenState(self.parent)
            else:
                self.next_state = BetweenFloorsNoDirectionState(self.parent)
        else:
            for i in range(0, NUMBER_OF_FLOORS - 1):
                if (orders[i] != 0) and (orders[i] < orders[i + 1]):
                    next_floor = i

            if next_floor < self.parent.elevator_link.get_floor():
                self.next_state = DownState(self.parent)
            else:
                self.next_state = UpState(self.parent)


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
        current_floor = self.parent.elevator_link.get_floor()
        for floor in range (current_floor, NUMBER_OF_FLOORS):
            for order_type in range (0, 3):
                if self.parent.elevator_link.get_order_button(floor, order_type):
                    if order_type == 0 or order_type == 2:
                        self.next_state = AtFloorDoorClosedState(self.parent)
                    else:
                        self.next_state = UpState(self.parent)

        # TODO await ?
            #  while (await self.parent.elevator_link.get_floor())[1] != 3:

        await asyncio.sleep(0.1)

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
        # TODO
        current_floor = self.parent.elevator_link.get_floor()
        while await self.parent.elevator_link.get_floor():

        for floor in range(current_floor, -1):
            for order_type in range(0, 3):
                if self.parent.elevator_link.get_order_button(floor, order_type):
                    if order_type == 1 or order_type == 2:
                        self.next_state = AtFloorDoorClosedState(self.parent)
                    else:
                        self.next_state = DownState(self.parent)

        # TODO await ?
        #  while (await self.parent.elevator_link.get_floor())[1] != 3:

        await asyncio.sleep(0.1)

    async def leave(self):
        assert self.next_state
        return self.next_state


class AtFloorDoorClosedState(State):
    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        self.parent.elevator_link.stop()
        floor = self.parent.elevator_link.get_floor()[2]
        # self.parent.elevator_link.set_floor_indicator(floor)
        await asyncio.sleep(1)

    async def process(self):
        if self.parent.elevator_link.get_stop_button():
            self.parent.elevator_link.set_stop_light()
            self.next_state = AtFloorDoorOpenState(self.parent)

        else:
            floor = self.parent.elevator_link.get_floor()[2]
            for order_type in range (0,3):
                if self.parent.elevator_link.get_order_button(floor, order_type)
                    self.next_state = AtFloorDoorOpenState(self.parent)
                else:
                    if go_to_new_floor():
                        self.next_state = TransitState(self.parent)
                    else:
                        self.next_state = AtFloorDoorClosedState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state


class AtFloorDoorOpenState(State):
    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        self.parent.elevator_link.set_door_light(1)
        await asyncio.sleep(1)

    async def process(self):
        if self.parent.elevator_link.get_obstruction_switch():
            self.next_state = AtFloorDoorOpenState(self.parent)

        else:
            await asyncio.sleep(3)
            self.next_state = AtFloorDoorClosedState(self.parent)

    async def leave(self):
        self.parent.elevator_link.set_door_light(0)
        assert self.next_state
        return self.next_state


class StateMachine:

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
        state_machine = StateMachine(elevator_link)
        await state_machine.run()

asyncio.run(main())