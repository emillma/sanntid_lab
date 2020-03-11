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
from os import system

logging.basicConfig(level=logging.DEBUG)


async def foo(l):
    while 1:
        system('clear')
        print(l)
        await asyncio.sleep(0.1)

async def main():
    global common_ledger, nl, task_creator, local_ledger
    common_ledger = CommonLedger(4)
    local_ledger = LocalLedger(4)
    async with ElevatorLink() as el, \
            NetworkLink(9000, common_ledger) as nl:

        task_creator = TaskCreator(el, local_ledger, common_ledger)
        await asyncio.gather(nl.run(), foo(local_ledger), task_creator.run())


asyncio.run(main())