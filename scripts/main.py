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
from state_machine3 import StateMachine
from light_handler import LightHandler
logging.basicConfig(format='[%(asctime)s %(filename)s:%(lineno)d] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.DEBUG)


async def printer(local, common):
    while 1:
        # print(print(chr(27) + "[2J"))
        print(local)
        # print(common)
        await asyncio.sleep(1)


async def main():
    global common_ledger, nl, task_creator, local_ledger
    common_ledger = CommonLedger(4)
    local_ledger = LocalLedger(4)
    logging.debug('got here')

    async with ElevatorLink() as el, \
        NetworkLink(9000, common_ledger,
                    update_rate=10, sendto=[9000]) as nl:

        sm = StateMachine(el, local_ledger, common_ledger)
        task_creator = TaskCreator(el, local_ledger, common_ledger)
        light_handler = LightHandler(el, local_ledger, common_ledger)
        await asyncio.gather(nl.run(),
                             task_creator.run(), sm.run(), light_handler.run())


asyncio.run(main())


