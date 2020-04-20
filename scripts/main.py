# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 20:53:46 2020

@author: user_id
"""

from elevator_link import ElevatorLink
import asyncio
import logging
from utils import now
from ledger_common import CommonLedger
from ledger_local import LocalLedger
from network_link import NetworkLink
from task_creator import TaskCreator
from state_machine2 import StateMachine
from light_handler import LightHandler
logging.basicConfig(format='[%(asctime)s %(filename)s:%(lineno)d] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


async def printer(local, common):
    while 1:
        return
        print(print(chr(27) + "[2J"))
        # print(local)
        print(common)
        await asyncio.sleep(0.5)


async def elevator(number):
    common_ledger = CommonLedger(4)
    local_ledger = LocalLedger(4)
    logging.debug('got here')

    async with ElevatorLink(port=15657 + number) as el, \
        NetworkLink(9000 + number, common_ledger,
                    update_rate=20, sendto=[9000, 9001]) as nl:

        sm = StateMachine(el, local_ledger, common_ledger, id = 1+ number)
        task_creator = TaskCreator(el, local_ledger, common_ledger)
        light_handler = LightHandler(el, local_ledger, common_ledger)
        await asyncio.gather(nl.run(), printer(local_ledger, common_ledger),
                             task_creator.run(), sm.run(), light_handler.run())

async def main():
    await asyncio.gather(elevator(0), elevator(1))

asyncio.run(main())


