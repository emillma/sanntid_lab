#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 16:55:19 2020.

@author: user_id


Husk a starte heissim før du kjører.

"""
from __future__ import annotations
from elevator_link import ElevatorLink

import itertools
import asyncio

from ledger_common import CommonLedger
from ledger_local import LocalLedger

from utils import now

SLEEPTIME = 0.1
class ButtonHandler:
    """Object used to create tasks from buttons and obstruction."""

    def __init__(self,
                 elevator_link: ElevatorLink,
                 local_ledger: LocalLedger,
                 common_ledger: CommonLedger):
        """Initialize the handler.

        Parameters
        ----------
        elevator_link : ElevatorLink

        local_ledger : LocalLedger

        common_ledger : CommonLedger


        Returns
        -------
        None.

        """
        self.elevator_link = elevator_link
        self.local_ledger = local_ledger
        self.common_ledger = common_ledger

    async def poll_buttons(self):
        """
        Poll all the buttons and add tasks to local_tasks and common_tasks.

        Returns
        -------
        None.

        """

        for floor, order in itertools.product(
                range(self.elevator_link.floor_n), range(3)):
            # Order: Up: 0, Down: 1, Cab: 2
            if (floor == 0 and order == 1
                    or floor == self.elevator_link.floor_n - 1
                    and order == 0):
                continue  # No point in polling invalid buttons
            retval, data = await self.elevator_link.get_order_button(floor,
                                                                     order)

            # Orders
            if retval is None and data == 1:
                if order in [0, 1]:
                    self.common_ledger.add_task_get(floor, order, now())
                if order == 2:
                    self.local_ledger.add_task_deliver(floor, now())

            # Stop
            retval, data = await self.elevator_link.get_stop_button()
            if retval is None:
                if data == 1:
                    self.local_ledger.add_stop(now())
                elif (data == 0
                      and now()-self.local_ledger.stop_continue_msgs[0] > 5e5):
                    self.local_ledger.add_continue(now())

            # Obstruction
            retval, data = await self.elevator_link.get_obstruction_switch()
            if retval is None:
                if data == 1:
                    self.local_ledger.add_block(now())
                elif data == 0:
                    self.local_ledger.add_deblock(now())

    async def run(self):
        """
        Run the task crator function.

        Returns
        -------
        None.

        """

        while 1:
            await self.poll_buttons()
            await asyncio.sleep(SLEEPTIME)