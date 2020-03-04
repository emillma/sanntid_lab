from elevator_link import ElevatorLink
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)

NUMBER_OF_FLOORS = 4

def stop_button_pressed():
    # TODO

    #
    # return get_stop_button(self)
    return 0


def elevator_at_floor():
    for floor in range (0, NUMBER_OF_FLOORS):
        if(read_floor_sensor(floor)):
            return 1
    return 0


def elevator_at_new_floor():
    # TODO
    return 1


def stop_at_floor():
    # TODO
    return 1


def obstruction():
    # TODO
    # return get_obstruction_switch(self)
    return 0


def open_door():
    # TODO
    return 0


def go_to_new_floor():
    # TODO
    return 1


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
        if not stop_button_pressed():
            self.next_state = TransitState(self.parent)
        else:
            self.next_state = BetweenFloorsNoDirectionState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state


class TransitState(State):
    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        # TODO Logic for up or down
        #  self.parent.elevator_link.go_up() / self.parent.elevator_link.go_down()
        await asyncio.sleep(1)

    async def process(self):
        if stop_button_pressed():
            self.parent.elevator_link.set_stop_light()
            if elevator_at_floor():
                self.next_state = AtFloorDoorOpenState(self.parent)
            else:
                self.next_state = BetweenFloorsNoDirectionState(self.parent)
        else:
            if elevator_at_new_floor():
                # TODO Set floor light ??
                if stop_at_floor():
                    self.next_state = AtFloorDoorClosedState(self.parent)
                else:
                    self.next_state = TransitState(self.parent)
            else:
                self.next_state = TransitState(self.parent)

    async def leave(self):
        assert self.next_state
        return self.next_state


class AtFloorDoorClosedState(State):
    def __init__(self, parent):
        self.parent = parent
        self.next_state = None

    async def enter(self):
        self.parent.elevator_link.stop()
        self.parent.elevator_link.set_door_light(0)
        await asyncio.sleep(1)

    async def process(self):
        if self.parent.elevator_link.get_stop_button():
            self.parent.elevator_link.set_stop_light()
            self.next_state = AtFloorDoorOpenState(self.parent)

        else:
            if open_door():
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