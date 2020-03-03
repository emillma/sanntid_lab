from time import clock
#from elevator_link import get_stop_button, get_obstruction_switch

#EVENTS
def stop_button_pressed():
    # TODO
    return 0

def elevator_at_floor():
    # TODO
    return 0

def elevator_at_new_floor():
    # TODO
    return 0

def stop_at_floor():
    # TODO
    return 0

def obstruction():
    # TODO

    return 0

def go_to_new_floor():
    # TODO
    return 1

def open_door():
    # TODO
    return 0

#TRANSITION
class Transition(object):
    def __init__(self, toState):
        self.toState = toState

    def Execute(self):
        print("Transitioning")

#EXAMPLE STATE OBJECT
class State(object):
    def __init__(self, elevator_state_machine):
        self.elevator_state_machine = elevator_state_machine
        self.timer = 0
        self.startTime = 0

    def Enter(self):
        self.timer = 3
        self.startTime = int(clock())

    def Execute(self):
        pass

    def Exit(self):
        pass


# STATES
class BetweenFloorsNoDirection(State):
    def __init__(self, elevator_state_machine):
        super(BetweenFloorsNoDirection, self).__init__(elevator_state_machine)

    def Enter(self):
        super(BetweenFloorsNoDirection, self).Enter()
        print('BetweenFloorsNoDirection\n')
    def Execute(self):
        if not stop_button_pressed():
            self.elevator_state_machine.ToTransition("toTransit")
        else:
            self.elevator_state_machine.ToTransition("toSelf")
    def Exit(self):
        pass

class Transit(State):
    def __init__(self, elevator_state_machine):
        super(Transit, self).__init__()

    def Enter(self):
        super(Transit, self).Enter()
        print('Transit\n')
    def Execute(self):

        if not stop_button_pressed():
            if elevator_at_new_floor():
                if stop_at_floor():
                    self.elevator_state_machine.ToTransition("toAtFloorDoorClosed")
                else:
                    self.elevator_state_machine.ToTransition("toTransit")
            else:
                self.elevator_state_machine.ToTransition("toTransit")
        else:
            self.elevator_state_machine.ToTransition("toSelf")

    def Exit(self):
        pass


class AtFloorDoorClosed(State):
    def __init__(self, elevator_state_machine):
        super(AtFloorDoorClosed, self).__init__()

    def Enter(self):
        super(AtFloorDoorClosed, self).Enter()
        print('AtFloorDoorClosed\n')
    def Execute(self):

        if not stop_button_pressed():
            if elevator_at_new_floor():
                if open_door():
                    self.elevator_state_machine.ToTransition("toAtFloorDoorOpen")
                else:
                    if go_to_new_floor():
                        self.elevator_state_machine.ToTransition("toTransit")
                    else:
                        self.elevator_state_machine.ToTransition("toSelf")
            else:
                self.elevator_state_machine.ToTransition("toTransit")
        else:
            self.elevator_state_machine.ToTransition("toAtFloorDoorOpen")

    def Exit(self):
        pass

class AtFloorDoorOpen(State):
    def __init__(self, elevator_state_machine):
        super(AtFloorDoorOpen, self).__init__()

    def Enter(self):
        super(AtFloorDoorOpen, self).Enter()
        print('AtFloorDoorOpen\n')
    def Execute(self):
        #TODO wait 3 seconds
        if not obstruction():
            self.elevator_state_machine.ToTransition("toAtFloorDoorClosed")
        else:
            self.elevator_state_machine.ToTransition("toSelf")

    def Exit(self):
        pass
    
#ELEVATOR STATE MACHINE

class ElevatorStateMachine(object):
    def __init__(self):
        self.states = {}
        self.transitions = {}
        self.cur_state = None
        self.prev_state = None
        self.trans = None

    def AddTransition(self, trans_name, transition):
        self.transitions[trans_name] = transition

    def AddState(self, state_name, state):
        self.states[state_name] = state

    def SetState(self, state_name):
        self.prev_state = self.cur_state
        self.cur_state = self.states[state_name]

    def ToTransition(self, to_trans):
        self.trans = self.transitions[to_trans]

    def Execute(self):
        if self.trans:
            self.cur_state.Exit()
            self.trans.Execute()
            self.SetState(self.trans.toState)
            self.cur_state.Enter()
            self.trans = None
        self.cur_state.Execute()

class Elevator(object):
    def __init__(self, char):
        self.char = char
        self.elevator_state_machine = elevator_state_machine(self)

        self.elevator_state_machine.AddState("BetweenFloorsNoDirection", BetweenFloorsNoDirection(self.elevator_state_machine))
        self.elevator_state_machine.AddState("Transit", Transit(self.elevator_state_machine))
        self.elevator_state_machine.AddState("AtFloorDoorClosed", AtFloorDoorClosed(self.elevator_state_machine))
        self.elevator_state_machine.AddState("AtFloorDoorOpen", AtFloorDoorOpen(self.elevator_state_machine))

        self.elevator_state_machine.AddTransition("toBetweenFloorsNoDirection", Transition("BetweenFloorsNoDirection"))
        self.elevator_state_machine.AddTransition("toTransit", Transition("Transit"))
        self.elevator_state_machine.AddTransition("toAtFloorDoorClosed", Transition("AtFloorDoorClosed"))
        self.elevator_state_machine.AddTransition("toAtFloorDoorOpen", Transition("AtFloorDoorOpen"))

        self.elevator_state_machine.SetState("BetweenFloorsNoDirection")

    def SetState(self, stateName):
            self.curState = self.states[stateName]

    def Transist(self):
            self.elevator_state_machine.Transit()
    def Execute(self):
        self.elevator_state_machine.Execute()


def main():

    elevator = Elevator.__init__()


    #while 1: