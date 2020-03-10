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
from utils import toclock, now
import json


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


def merge_in_select(old, select_msg, limit=1e6, hyst = 1e5):
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
            if old[1] - hyst > select_msg[1]:
                old[:] = select_msg
        else:
            # If the timestamp of a is smaller
            if old[0] < select_msg[0]:
                old[:] = select_msg
    return old


def merge_in_deselect(old, deselect_msg):

    # If the old one is None, set new one
    if old[1, 0] == 0:
        old[1, :] = deselect_msg
        return old

    # if the id of the deselect is not the same as current select, return
    elif deselect_msg[2] != old[0, 2]:
        return old

    else:
        # If the timestamp of a is smaller
        if old[1, 0] < deselect_msg[0]:
            old[1, :] = deselect_msg
        return old


class CommonLedger:

    def __init__(self, number_of_floors=None, json_data=None,
                 get_done_msgs=None, select_deselect_msgs=None):

        if json_data is not None:
            data = json.loads(json_data.decode())
            assert data['type'] == 'CommonLedger', TypeError
            self.NUMBER_OF_FLOORS = np.array(data['NUMBER_OF_FLOORS'],
                                             dtype=np.int64)
            self._get_done_msgs = np.array(data['_get_done_msgs'],
                                          dtype=np.int64)
            self._select_deselect_msgs = np.array(data['_select_deselect_msgs'],
                                                 dtype=np.int64)

        else:
            assert number_of_floors
            self.NUMBER_OF_FLOORS = number_of_floors

            # floor, up/down, get/done
            if not np.any(get_done_msgs):
                self._get_done_msgs = np.zeros((number_of_floors, 2, 2),
                                              dtype=np.int64)
            else:
                self._get_done_msgs = get_done_msgs

            # floor, up/down, select/deselect, stamp/etd/id
            if not np.any(select_deselect_msgs):
                self._select_deselect_msgs = np.zeros(
                    (number_of_floors, 2, 2, 3), dtype=np.int64)
            else:
                self._select_deselect_msgs = select_deselect_msgs

    def __repr__(self):
        out = 'Get Done Messages\n'
        for floor in range(self._get_done_msgs.shape[0]):
            for ud in [0, 1]:
                out += f'Floor {floor:2d}, '
                out += 'UP:  ' if not ud else 'DOWN:'
                out += '    '
                time_get = toclock(self._get_done_msgs[floor, ud, 0])
                time_done = toclock(self._get_done_msgs[floor, ud, 1])
                out += f'GET: {time_get}     DONE: {time_done}'
                out += '\n'
        out += '\nSelect Deselect Messages\n'
        for floor in range(self._get_done_msgs.shape[0]):
            for ud in [0, 1]:
                out += f'Floor {floor:2d}, '
                out += 'UP:  ' if not ud else 'DOWN:'
                out += '    '
                select_stamp = toclock(self._select_deselect_msgs[
                    floor, ud, 0, 0])
                select_id = self._select_deselect_msgs[floor, ud, 0, 1]
                select_etd = toclock(self._select_deselect_msgs[
                    floor, ud, 0, 2])
                deselect_stamp = toclock(self._select_deselect_msgs[
                    floor, ud, 1, 0])
                deselect_id = self._select_deselect_msgs[floor, ud, 1, 1]

                out += f'Select: {select_stamp}  {select_id:20d}  '
                out += f'{select_etd}     '
                out += f'Deselect: {deselect_stamp}  {deselect_id:20d}'
                out += '\n'

        return out

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other: CommonLedger):
        assert isinstance(other, CommonLedger)
        return (np.array_equal(self._get_done_msgs, other._get_done_msgs) and
                np.array_equal(self._select_deselect_msgs,
                               other._select_deselect_msgs)
                )

    def __add__(self, other):
        assert isinstance(other, CommonLedger)
        get_done_msgs = self._get_done_msgs.copy()
        select_deselect_msgs = self._select_deselect_msgs.copy()
        for floor in range(self.NUMBER_OF_FLOORS):
            for direction in [0, 1]:  # [up, down]

                merge_in_done(
                    get_done_msgs[floor, direction],
                    other._get_done_msgs[floor, direction, 1])

                merge_in_get(
                    get_done_msgs[floor, direction],
                    other._get_done_msgs[floor, direction, 0])

                merge_in_deselect(
                    select_deselect_msgs[floor, direction, :, :],
                    other._select_deselect_msgs[floor, direction, 1, :])

                merge_in_select(
                    select_deselect_msgs[floor, direction, 0, :],
                    other._select_deselect_msgs[floor, direction, 0, :])

        return CommonLedger(self.NUMBER_OF_FLOORS,
                            get_done_msgs = get_done_msgs,
                            select_deselect_msgs = select_deselect_msgs)

    def __iadd__(self, other):
        if isinstance(other, CommonLedger):
            return self.__add__(other)
        elif isinstance('hello'.encode(), bytes):
            return self.__add__(CommonLedger(json_data=other))

    def encode(self):
        data = {}
        data['type'] = 'CommonLedger'
        data['NUMBER_OF_FLOORS'] = self.NUMBER_OF_FLOORS
        data['_get_done_msgs'] = self._get_done_msgs.tolist()
        data['_select_deselect_msgs'] = self._select_deselect_msgs.tolist()
        return json.dumps(data).encode()

    def add_task_get(self, floor, ud, timestamp):
        # up: 0 down: 1
        assert floor <= self.NUMBER_OF_FLOORS
        merge_in_get(self._get_done_msgs[floor, ud, :], timestamp)

    def add_task_done(self, floor, ud, timestamp):
        # up: 0 down: 1
        assert floor <= self.NUMBER_OF_FLOORS
        merge_in_done(self._get_done_msgs[floor, ud, :], timestamp)

    def add_select(self, floor, ud, timestamp, id, etd):
        select = np.array([timestamp, id, etd], dtype=np.int64)
        merge_in_select(self._select_deselect_msgs[floor, ud, 0, :], select)

    def add_deselect(self, floor, ud, timestamp, id):
        deselect = np.array([timestamp, id, 0], dtype=np.int64)
        merge_in_deselect(self._select_deselect_msgs[floor, ud, :, :],
                          deselect)

    def get_available_jobs(self):
        valid_stamp = (self._get_done_msgs[:, :, 0]
                       > self._get_done_msgs[:, :, 1])
        return valid_stamp

    def get_selected_jobs(self, id):
        # where the select timestamp is greater than deselect timestamp
        valid_stamp = (self._select_deselect_msgs[:, :, 0, 0]
                       > self._select_deselect_msgs[:, :, 1, 0])

        valid_id = self._select_deselect_msgs[:, :, 0, 1] == id

        return valid_stamp * valid_id * self.get_available_jobs()



if __name__ == '__main__':
    a = CommonLedger(4)
    b = CommonLedger(4)
    # a.add_task_get(1, 0, time.time() * 1e6)
    b.add_task_done(1, 0, time.time() * 1e6 + 1e6)
    b.add_task_get(1, 0, time.time() * 1e6 + 2e6)
    a.add_task_done(1, 0, time.time() * 1e6)
    a.add_select(1, 0, now(), hash(1.2), now() + 1000000)
    a.add_deselect(1, 0, now(), hash(1.1))
    c = a + b
