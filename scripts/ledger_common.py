# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 16:15:09 2020

waiting for error fix in Numba
https://github.com/numba/numba/issues/5100
@author: user_id
"""

from __future__ import annotations
import numpy as np
import time
from utils import toclock, stamp


def merge_in_get(get_done, new_timestamp):
    if not get_done[0]:
        get_done[0] = new_timestamp
    # If the old message is invalid
    elif get_done[0] < get_done[1]:
        if new_timestamp > get_done[1]:
            get_done[0] = new_timestamp
    # If the old message is valid
    else:
        # If the new message also is valid
        if new_timestamp > get_done[1]:
            get_done[0] = np.minimum(get_done[0], new_timestamp)


def merge_in_done(get_done, new_timestamp):
    get_done[1] = np.maximum(get_done[1], new_timestamp)


def merge_in_select(old, select_msg, limit=1e6):
    # If only one os valid
    if bool(old[0]) != bool(select_msg[0]):
        # A is default, so if it is b, swap
        if bool(select_msg[0]):
            old[:] = select_msg

    # If both are valid
    elif old[0] and select_msg[0]:
        # If the timestamps are similar
        if (np.abs(old[0] - select_msg[0]) < limit):
            # If the ETD of a is larger than b, swap
            if old[1] > select_msg[1]:
                old[:] = select_msg
        else:
            # If the timestamp of a is smaller
            if old[0] < select_msg[0]:
                old[:] = select_msg
    return old


def merge_in_deselect(old, deselect_msg, limit=1e6):
    # If only one os valid
    if bool(old[0]) != bool(deselect_msg[0]):
        # A is default, so if it is b, swap

        if bool(deselect_msg[0]):
            old[:] = deselect_msg

    # If both are valid
    elif old[0] and deselect_msg[0]:
        # If the timestamps are similar
        if (np.abs(old[0] - deselect_msg[0]) < limit):
            # If the ETD of a is smaller than b, swap
            if old[1] < deselect_msg[1]:
                old[:] = deselect_msg
        else:
            # If the timestamp of a is smaller
            if old[0] < deselect_msg[0]:
                old[:] = deselect_msg
    return old


class CommonLedger:

    def __init__(self, number_of_floors,
                 get_done_msgs=None, select_deselect_msgs=None):

        self.NUMBER_OF_FLOORS = number_of_floors
        # floor, up/down, get/done
        if not np.any(get_done_msgs):
            self.get_done_msgs = np.zeros((number_of_floors, 2, 2),
                                          dtype=np.int64)
        else:
            self.get_done_msgs = get_done_msgs

        # floor, up/down, select/deselect, stamp/etd/id
        if not np.any(select_deselect_msgs):
            self.select_deselect_msgs = np.zeros((number_of_floors, 2, 2, 3),
                                                 dtype=np.int64)
        else:
            self.select_deselect_msgs = select_deselect_msgs

    def __repr__(self):
        out = 'Get Done Messages\n'
        for floor in range(self.get_done_msgs.shape[0]):
            for ud in [0, 1]:
                out += f'Floor {floor:2d}, '
                out += 'UP:  ' if not ud else 'DOWN:'
                out += '    '
                time_get = toclock(self.get_done_msgs[floor, ud, 0])
                time_done = toclock(self.get_done_msgs[floor, ud, 1])
                out += f'GET: {time_get}     DONE: {time_done}'
                out += '\n'
        out += '\nSelect Deselect Messages\n'
        for floor in range(self.get_done_msgs.shape[0]):
            for ud in [0, 1]:
                out += f'Floor {floor:2d}, '
                out += 'UP:  ' if not ud else 'DOWN:'
                out += '    '
                select_stamp = toclock(self.select_deselect_msgs[
                    floor, ud, 0, 0])
                select_id = self.select_deselect_msgs[floor, ud, 0, 1]
                select_etd = toclock(self.select_deselect_msgs[
                    floor, ud, 0, 2])
                deselect_stamp = toclock(self.select_deselect_msgs[
                    floor, ud, 1, 0])
                deselect_id = self.select_deselect_msgs[floor, ud, 1, 1]

                out += f'Select: {select_stamp}  {select_id:20d}  '
                out +=  f'{select_etd}     '
                out += f'Deselect: {deselect_stamp}  {deselect_id:20d}'
                out += '\n'

        return out

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other: CommonLedger):
        assert isinstance(other, CommonLedger)
        return (np.array_equal(self.get_done_msgs, other.get_done_msgs) and
                np.array_equal(self.select_deselect_msgs,
                               other.select_deselect_msgs)
                )

    def __add__(self, other):
        assert isinstance(other, CommonLedger)
        get_done_msgs = self.get_done_msgs.copy()
        select_deselect_msgs = self.select_deselect_msgs.copy()
        for floor in range(self.NUMBER_OF_FLOORS):
            for direction in [0, 1]:  # [up, down]

                merge_in_done(
                    get_done_msgs[floor, direction],
                    other.get_done_msgs[floor, direction, 1])

                merge_in_get(
                    get_done_msgs[floor, direction],
                     other.get_done_msgs[floor, direction, 0])

                merge_in_deselect(
                    select_deselect_msgs[floor, direction, 1, :],
                    other.select_deselect_msgs[floor, direction, 1, :])

                merge_in_select(
                    select_deselect_msgs[floor, direction, 0, :],
                    other.select_deselect_msgs[floor, direction, 0, :])

        return CommonLedger(self.NUMBER_OF_FLOORS, get_done_msgs,
                            select_deselect_msgs)

    def add_task_get(self, floor, ud, timestamp):
        # up: 0 down: 1
        assert floor <= self.NUMBER_OF_FLOORS
        merge_in_get(self.get_done_msgs[floor, ud, :], timestamp)

    def add_task_done(self, floor, ud, timestamp):
        # up: 0 down: 1
        assert floor <= self.NUMBER_OF_FLOORS
        merge_in_done(self.get_done_msgs[floor, ud, :], timestamp)

    def add_select(self, floor, ud, timestamp, id, etd):
        select = np.array([timestamp, id, etd], dtype=np.int64)
        merge_in_select(self.select_deselect_msgs[floor, ud, 0, :], select)

    def add_deselect(self, floor, ud, timestamp, id):
        deselect = np.array([timestamp, id, 0], dtype=np.int64)
        merge_in_deselect(self.select_deselect_msgs[floor, ud, 1, :], deselect)

if __name__ == '__main__':
    a = CommonLedger(4)
    b = CommonLedger(4)
    a.add_task_get(1, 0, time.time() * 1e6)
    b.add_task_get(1, 0, time.time() * 1e6)
    b.add_task_done(1, 0, time.time() * 1e6)
    a.add_task_done(1, 0, time.time() * 1e6)
    a.add_select(1, 0, stamp(), hash(1.1), stamp() + 1000000)
    a.add_deselect(1, 0, stamp(), hash(1.1))
    c = a + b