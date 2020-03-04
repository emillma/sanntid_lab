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

logging.basicConfig(level=logging.DEBUG)

async def main():
    common_ledger = CommonLedger(4)
    async with ElevatorLink() as el, \
            NetworkLink(9000, common_ledger) as nl:

        await nl.run()


asyncio.run(main())