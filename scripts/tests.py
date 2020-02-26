# -*- coding: utf-8 -*-
"""
Created on Sun Feb 23 20:53:46 2020

@author: user_id
"""

from elevator_link import ElevatorLink
import asyncio
import logging
logging.basicConfig(level=logging.DEBUG)
import random



async def chain(*corutines):
    for corutine in corutines:
        await corutine

async def elevator_link_stress_test():
    async with ElevatorLink() as el:
        test_commands = [(el.get_floor,),
                         (el.get_stop_button,),
                         (el.set_door_light, 1,),
                         (el.go_up,),
                         (el.go_down,)]
        tasks = []
        for _ in range(20):
            task, *args = random.choice(test_commands)
            # task, *args = test_commands[_]
            tasks.append(chain(asyncio.sleep(random.random()*10),
                               task(*args)))

        std =  asyncio.gather(*tasks)
        await std



async def main():
    async with ElevatorLink() as el:
        while 1:
            await asyncio.sleep(1)
            print(await el.get_floor())

# asyncio.run(main())


asyncio.run(elevator_link_stress_test())