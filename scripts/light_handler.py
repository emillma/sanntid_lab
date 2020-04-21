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

SLEEPTIME = 0.02


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

    async def run(self):
        """Run the coroutine."""
        while True:
            local_jobs = self.local_ledger.jobs
            common_jobs = self.common_ledger.jobs
            for floor, value in enumerate(local_jobs):
                await self.elevator_link.set_button_light(floor, 2,
                                                          1 if value else 0)

            for floor, direction in enumerate(common_jobs):
                up, down = direction
                await self.elevator_link.set_button_light(floor, 0,
                                                          1 if up else 0)
                await self.elevator_link.set_button_light(floor, 1,
                                                          1 if down else 0)

            await asyncio.sleep(SLEEPTIME)
