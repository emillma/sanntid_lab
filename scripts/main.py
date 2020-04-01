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

import nest_asyncio
nest_asyncio.apply()


logging.basicConfig(format='[%(filename)s:%(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d:%H:%M:%S',
                    level=logging.INFO)


async def foo(x):
    return
    while 1:
        print(x)
        await asyncio.sleep(1)


async def main():
    global common_ledger, nl, task_creator, local_ledger
    common_ledger = CommonLedger(4)
    local_ledger = LocalLedger(4)
    async with ElevatorLink() as el, \
        NetworkLink(9000, common_ledger,
                    update_rate=10, sendto=[9000, 9001]) as nl:

        task_creator = TaskCreator(el, local_ledger, common_ledger)
        await asyncio.gather(nl.run(), foo(common_ledger), task_creator.run())

asyncio.run(main())
