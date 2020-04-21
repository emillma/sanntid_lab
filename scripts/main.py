# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 20:53:46 2020.

@author: user_id
"""

import asyncio
import logging

from ledger_common import CommonLedger
from ledger_local import LocalLedger

from elevator_link import ElevatorLink
from network_link import NetworkLink

from state_machine import StateMachine

from task_creator import ButtonHandler
from light_handler import LightHandler


logging.basicConfig(format='[%(asctime)s %(filename)s:%(lineno)d] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)


async def elevator(elevator_number):
    """Run a elevator."""
    common_ledger = CommonLedger(number_of_floors=4)
    local_ledger = LocalLedger(number_of_floors=4)

    network_kwargs = {'port': 9000 + elevator_number,
                      'common_ledger': common_ledger,
                      'update_rate': 20,
                      'sendto': [9000, 9001, 9002]}

    #  open connection with elevator ant udp ports
    async with \
            ElevatorLink(port=15657 + elevator_number) as elevator_link, \
            NetworkLink(**network_kwargs) as network_link:

        state_machine = StateMachine(elevator_link,
                                     local_ledger,
                                     common_ledger,
                                     id_=1 + elevator_number)

        task_creator = ButtonHandler(elevator_link,
                                     local_ledger,
                                     common_ledger)

        light_handler = LightHandler(elevator_link,
                                     local_ledger,
                                     common_ledger)

        #  start all the differnet coroutines belonging to one elevator
        await asyncio.gather(network_link.run(),
                             task_creator.run(),
                             state_machine.run(),
                             light_handler.run())


async def main():
    """Run multiple elevators."""
    #  start multiple elevators
    await asyncio.gather(
        elevator(0),
        elevator(1),
        elevator(2))

asyncio.run(main())
