# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 20:53:46 2020

@author: user_id
"""

from elevator_link import ElevatorLink
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)
async def main():
    async with ElevatorLink() as el:
        while 1:
            await asyncio.sleep(1)
            print(await el.get_floor())


asyncio.run(main())