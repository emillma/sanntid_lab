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


STAMP = 0
ETD = 1
ID = 2

UP = 0
DOWN = 1

GET = 0
DONE = 1

SELECT_TIMEOUT = 5e6
def merge_in_get(get_done, new_timestamp):
    if not get_done[GET]:
        get_done[GET] = new_timestamp
    # If the old message is invalid
    elif get_done[GET] < get_done[DONE]:
        if new_timestamp > get_done[DONE]:
            get_done[GET] = new_timestamp
    # If the old message is valid
    else:
        # If the new message also is valid
        if new_timestamp > get_done[DONE]:
            get_done[GET] = np.minimum(get_done[GET], new_timestamp)


def merge_in_done(get_done, new_timestamp):
    get_done[DONE] = np.maximum(get_done[DONE], new_timestamp)


def merge_in_select(old, select_msg, hyst=1e6):
    # if they have the same id
    if old[ID] == select_msg[ID]:
        # use the most recent
        if select_msg[STAMP] > old[STAMP]:
            old[:] = select_msg

    # If only one os valid
    elif bool(old[STAMP]) != bool(select_msg[STAMP]):
        # A is default, so if it is b, swap
        if bool(select_msg[STAMP]):
            old[:] = select_msg

    # If both are valid
    elif old[STAMP] and select_msg[STAMP]:
        # If the timestamps are similar
        if (np.abs(old[STAMP] - select_msg[STAMP]) < SELECT_TIMEOUT):
            # If the ETD of a is larger than b, swap
            if old[ETD] - hyst > select_msg[ETD]:
                old[:] = select_msg
        else:
            # If the timestamp of a is smaller
            if old[STAMP] < select_msg[STAMP]:
                old[:] = select_msg


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
            self._select_msgs = np.array(data['_select_msgs'],
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

            # floor, up/down, stamp/etd/id
            if not np.any(select_deselect_msgs):
                self._select_msgs = np.zeros(
                    (number_of_floors, 2, 3), dtype=np.int64)
            else:
                self._select_msgs = select_deselect_msgs
        self.remove_old()

    def __repr__(self):
        self.remove_old()
        out = 'Get Done Messages\n'
        for floor in range(self._get_done_msgs.shape[0]):
            for ud in [UP, DOWN]:
                out += f'Floor {floor:2d}, '
                out += 'UP:  ' if not ud else 'DOWN:'
                out += '    '
                time_get = toclock(self._get_done_msgs[floor, ud, GET])
                time_done = toclock(self._get_done_msgs[floor, ud, DONE])
                out += f'GET: {time_get}     DONE: {time_done}'
                out += '\n'
        out += '\nSelect Deselect Messages\n'
        for floor in range(self._get_done_msgs.shape[0]):
            for ud in [UP, DOWN]:
                out += f'Floor {floor:2d}, '
                out += 'UP:  ' if not ud else 'DOWN:'
                out += '    '
                select_stamp = toclock(self._select_msgs[
                    floor, ud, STAMP])
                select_id = self._select_msgs[floor, ud, ID]
                select_etd = toclock(self._select_msgs[
                    floor, ud, ETD])

                out += f'Select: {select_stamp}  {select_etd}  '
                out += f'{select_id:20d} \n'

        return out

    def __str__(self):
        return self.__repr__()

    def __eq__(self, other: CommonLedger):
        assert isinstance(other, CommonLedger)
        return (np.array_equal(self._get_done_msgs, other._get_done_msgs) and
                np.array_equal(self._select_msgs,
                               other._select_msgs)
                )

    def __add__(self, other):
        assert isinstance(other, CommonLedger)
        get_done_msgs = self._get_done_msgs.copy()
        select_deselect_msgs = self._select_msgs.copy()
        for floor in range(self.NUMBER_OF_FLOORS):
            for direction in [UP, DOWN]:  # [up, down]

                merge_in_done(
                    get_done_msgs[floor, direction],
                    other._get_done_msgs[floor, direction, DONE])

                merge_in_get(
                    get_done_msgs[floor, direction],
                    other._get_done_msgs[floor, direction, GET])

                merge_in_select(
                    select_deselect_msgs[floor, direction, :],
                    other._select_msgs[floor, direction, :])

        return CommonLedger(self.NUMBER_OF_FLOORS,
                            get_done_msgs = get_done_msgs,
                            select_deselect_msgs = select_deselect_msgs)

    def __iadd__(self, other):
        if isinstance(other, bytes):
            other = CommonLedger(json_data=other)
        assert isinstance(other, CommonLedger)
        for floor in range(self.NUMBER_OF_FLOORS):
            for direction in [0, 1]:  # [up, down]

                merge_in_done(
                    self._get_done_msgs[floor, direction],
                    other._get_done_msgs[floor, direction, DONE])

                merge_in_get(
                    self._get_done_msgs[floor, direction],
                    other._get_done_msgs[floor, direction, GET])

                merge_in_select(
                    self._select_msgs[floor, direction, :],
                    other._select_msgs[floor, direction, :])
        self.remove_old()
        return self

    def encode(self):
        self.remove_old()
        data = {}
        data['type'] = 'CommonLedger'
        data['NUMBER_OF_FLOORS'] = self.NUMBER_OF_FLOORS
        data['_get_done_msgs'] = self._get_done_msgs.tolist()
        data['_select_msgs'] = self._select_msgs.tolist()
        return json.dumps(data).encode()

    def add_task_get(self, floor, ud, timestamp=None):
        # up: 0 down: 1
        if timestamp is None:
            timestamp = now()
        assert floor <= self.NUMBER_OF_FLOORS
        merge_in_get(self._get_done_msgs[floor, ud, :], timestamp)

    def add_task_done(self, floor, ud, timestamp=None):
        # up: 0 down: 1
        if timestamp is None:
            timestamp = now()
        assert floor <= self.NUMBER_OF_FLOORS
        merge_in_done(self._get_done_msgs[floor, ud, :], timestamp)

    def add_select(self, floor, ud, etd, id,  timestamp=None):
        if timestamp is None:
            timestamp = now()
        select = np.array([timestamp, etd, id], dtype=np.int64)
        merge_in_select(self._select_msgs[floor, ud, :], select)

    def remove_old(self):
        old = now() - self._select_msgs[:, :, STAMP] > SELECT_TIMEOUT
        self._select_msgs[np.where(old)] = (0, 0, 0)

    @property
    def jobs(self):
        has_task = (self._get_done_msgs[:, :, GET]
                    > self._get_done_msgs[:, :, DONE])
        return np.where(has_task,
                        self._get_done_msgs[:, :, GET],
                        0)
    @property
    def available_jobs(self):
        has_task = (self._get_done_msgs[:, :, GET]
                    > self._get_done_msgs[:, :, DONE])
        self.remove_old()
        not_selected = self._select_msgs[:, :, STAMP] == 0

        return np.where(has_task * not_selected,
                        self._get_done_msgs[:, :, GET],
                        0)

    def get_selected_jobs(self, id):
        has_task = (self._get_done_msgs[:, :, GET]
                    > self._get_done_msgs[:, :, DONE])
        # where the select timestamp is greater than deselect timestamp
        self.remove_old()
        valid_id = self._select_msgs[:, :, ID] == id

        return np.where(has_task * valid_id,
                        self._get_done_msgs[:, :, GET],
                        0)

    def remove_selection(self, floor, direction, id):
        if id == self._select_msgs[floor, direction, ID]:
            self._select_msgs[floor, direction, :] = (0, 0, 0)


if __name__ == '__main__':
    a = CommonLedger(4)
    id1 = 100
    id2 = 200
    a.add_task_get(1,0)
    a.add_select(1, 0, now(), id1)
    print(a.get_selected_jobs(id1))
    # a.add_deselect(1, 0, now(), hash(1.1))
