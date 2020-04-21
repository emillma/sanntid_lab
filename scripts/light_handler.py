# -*- coding: utf-8 -*-
"""
Created on Fri Apr 17 16:21:30 2020.

@author: user_id
"""
from __future__ import annotations

import asyncio

from elevator_link import ElevatorLink
from ledger_common import CommonLedger
from ledger_local import LocalLedger

SLEEPTIME = 0.1

UP = 0
DOWN = 1
DELIVER = 2

OFF = 0
ON = 1



class LightHandler:
    """Object used to take care of turning on and turning off the lights.

    Exept floor light, which is handled by the StateMachine
    """

    def __init__(self, elevator_link: ElevatorLink,
                 local_ledger: LocalLedger,
                 common_ledger: CommonLedger):

        self.elevator_link = elevator_link
        self.local_ledger = local_ledger
        self.common_ledger = common_ledger
        self.previous_local = None
        self.previous_common = None

    async def run(self):
        """Run the coroutine."""
        while True:
            local_tasks = self.local_ledger.tasks.astype(bool)
            common_tasks = self.common_ledger.tasks.astype(bool)

            diff_local = local_tasks == self.previous_local
            for floor, value in enumerate(local_tasks):
                if diff_local[floor]:
                    await self.elevator_link.set_button_light(
                        floor, DELIVER, ON if value else OFF)

            self.previous_local = local_tasks
            diff_common = common_tasks == self.previous_common
            for floor, direction in enumerate(common_tasks):
                up, down = direction
                if diff_common[floor, int(up)]:
                    await self.elevator_link.set_button_light(
                        floor, UP, ON if up else OFF)

                if diff_common[floor, int(down)]:
                    await self.elevator_link.set_button_light(
                        floor, DOWN, ON if down else OFF)
            self.previous_common = common_tasks

            await asyncio.sleep(SLEEPTIME)
