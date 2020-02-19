from time import clock


#EVENTS
def stop_button_pressed()
    # TODO
    return 0

def elevator_at_floor()
    # TODO
    return 0

def elevator_at_new_floor()
    # TODO
    return 0

def stop_at_floor()
    # TODO
    return 0

def obstruction()
    # TODO
    return 0

def go_to_floor()
    # TODO
    return 1

def open_door()
    # TODO
    return 0

#TRANSITION
class Transition(object):
    def __init__(self, toState):
        self.toState = toState

    def Execute(self):
        print("Transitioning")

#STATE OBJECT
class State(object):
    def __init__(self, elevator_state_machine):
        self.elevator_state_machine = elevator_state_machine
        self.timer = 0
        self.startTime = 0

    def Enter(self):
        self.timer = 5
        self.startTime = int(clock())

    def Execute(self):
        pass

    def Exit(self):
        pass


# STATES
class BetweenFloorsNoDirection(State):
    def __init__(self, elevator_state_machine):
        super(BetweenFloorsNoDirection, self).__init__()

    def Enter(self):
        super(BetweenFloorsNoDirection, self).Enter()

    def Execute(self):
        if not stop_button_pressed():
            self.elevator_state_machine.ToTransition("toTransit")
        else:
            self.elevator_state_machine.ToTransition("toSelf")

class Transit(State):
    def __init__(self, elevator_state_machine):
        super(Transit, self).__init__()

    def Enter(self):
        super(Transit, self).Enter()

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


class AtFloorDoorClosed(State):
    def __init__(self, elevator_state_machine):
        super(AtFloorDoorClosed, self).__init__()

    def Enter(self):
        super(AtFloorDoorClosed, self).Enter()

    def Execute(self):

        if not stop_button_pressed():
            if elevator_at_new_floor():
                if open_door():
                    self.elevator_state_machine.ToTransition("toAtFloorDoorOpen")
                else:
                    if go_to_floor():
                        self.elevator_state_machine.ToTransition("toTransit")
                    else:
                        self.elevator_state_machine.ToTransition("toSelf")
            else:
                self.elevator_state_machine.ToTransition("toTransit")
        else:
            self.elevator_state_machine.ToTransition("toAtFloorDoorOpen")


class AtFloorDoorOpen(State):
    def __init__(self, elevator_state_machine):
        super(AtFloorDoorOpen, self).__init__()

    def Enter(self):
        super(AtFloorDoorOpen, self).Enter()

    def Execute(self):

        if not obstruction():
            self.elevator_state_machine.ToTransition("toAtFloorDoorClosed")
        else:
            self.elevator_state_machine.ToTransition("toSelf")


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
            self.curState.Exit()
            self.trans.Execute()
            self.SetState(self.trans.toState)
            self.cur_state.Enter()
            self.trans = None
        self.cur_state.Execute()

class Elevator(# TODO):
    def __init__(self):
        self.elevator_state_machine = elevator_state_machine(self)

        self.elevator_state_machine.AddState("BetweenFloorsNoDirection", BetweenFloorsNoDirection(self.elevator_state_machine))
        self.elevator_state_machine.AddState("Transit", Transit(self.elevator_state_machine))
        self.elevator_state_machine.AddState("AtFloorDoorClosed", AtFloorDoorClosed(self.elevator_state_machine))
        self.elevator_state_machine.AddState("AtFloorDoorOpen", AtFloorDoorOpen(self.elevator_state_machine))

        self.elevator_state_machine.AddTransition("toBetweenFloorsNoDirection", Transition("BetweenFloorsNoDirection")
        self.elevator_state_machine.AddTransition("toTransit", Transition("Transit")
        self.elevator_state_machine.AddTransition("toAtFloorDoorClosed", Transition("AtFloorDoorClosed")
        self.elevator_state_machine.AddTransition("toAtFloorDoorOpen", Transition("AtFloorDoorOpen")

        self.elevator_state_machine.SetState("BetweenFloorsNoDirection")
    def Execute(self):
        self.elevator_state_machine.Execute()


#class State:
    #def run(self):
   #     assert 0
  #  def next(self, input):
 #       assert 0

#class StateMachine:
    #def __init__(self, initialState):
      #  self.currentState = initialState
     #   self.currentState.run()






# EVENTS

#from enum import Enum, unique


#@unique
##   BetweenFloorsNoDirection = 0
  #  Transit = 1
   # AtFloorDoorClosed = 2
    #AtFloorDoorOpen = 3


