# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 16:15:09 2020


@author: user_id
"""

from __future__ import annotations
import numpy as np
from utils import toclock, now
import json
from typing import Optional


STAMP = 0
ETD = 1
ID = 2

UP = 0
DOWN = 1

GET = 0
DONE = 1

SELECT_TIMEOUT = 5e6


def merge_in_get(get_done, new_timestamp):
    """
    If the new get message is more relevant than the old one, the old one\
    is replaced byt the new one.

    Parameters
    ----------
    get_done : np.array[:]
        old get / done data
    new_timestamp : int
        new get request timestamp

    Returns
    -------
    None.

    """

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
    """
    If the new done message is more relevant than the old one, the old one\
    is replaced byt the new one.

    Parameters
    ----------
    get_done : np.array[:]
        old get / done data
    new_timestamp : int
        new done timestamp

    Returns
    -------
    None.

    """

    get_done[DONE] = np.maximum(get_done[DONE], new_timestamp)


def merge_in_select(old, select_msg, hyst=1e6):
    """
    If the new select message is more relevant than the old one, the old one\
    is replaced byt the new one.

    Parameters
    ----------
    old : np.array[:]
        old select message(timestamp, ETD (estimated time of delivery / id).
    select_msg : TYPE
        new select message (timestamp, ETD (estimated time of delivery / id).
    hyst : TYPE, optional
        DESCRIPTION. The default is 1e6.

    Returns
    -------
    None.

    """

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
    """
    This class handles all the tasks that the elevators might have in common
    AKA all the up and down requests. These requests are referred to as 'get'
    jobs.
    They are represented by a timestamp when the UP og DOWN was requested and a
    timestamp when a request was compleated (DONE).

    It also tracks which elevator has said it is handling what request with
    the select_msgs.
    They are represented by a timestamp when the select message was last made,
    an ETD (estimated time of delivery), and the ID of the elevator saying it
    has taken the order.

    Works in a similar way as the 'Set' data type where the most relevant task
    is kept track of when using the '+' or "+=" operators.
    """

    def __init__(self,
                 number_of_floors: int = 4,
                 json_data: Optional[bytes] = None,
                 get_done_msgs: Optional[np.array] = None,
                 select_deselect_msgs: Optional[np.array] = None):
        """
        Initialises the commonledger.

        It can be initialized as empty, from get and select messages or from
        a set of bytes (used in network communication).

        Parameters
        ----------
        number_of_floors : int, optional
            Number of floors supported.

        json_data : Optional[bytes], optional
            A json representation of a LocalLedger object.
            The default is None.

        get_done_msgs : Optional[np.array], optional
            An array representing the get and done messsages.
            The default is None.

        select_deselect_msgs : Optional[np.array], optional
            An array representing the select messsages.
            The default is None.
        """

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

    def __repr__(self) -> str:
        """
        Funcion used to display the ledger
        Exemple:

        Returns
        -------
        str
            Representation of the CommonLedger.

        """

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

    def __str__(self) -> str:
        """
        Funcion used to display the ledger as a string. Same as __repr__.

        Returns
        -------
        str
            Representation of the CommonLedger.
        """
        return self.__repr__()

    def __eq__(self, other: CommonLedger) -> bool:
        """
        Test if two CommonLedger are equal (==).

        Parameters
        ----------
        other : CommonLedger

        Returns
        -------
        bool
            True if their data is the same, else False.

        """
        assert isinstance(other, CommonLedger)
        return (np.array_equal(self._get_done_msgs, other._get_done_msgs) and
                np.array_equal(self._select_msgs,
                               other._select_msgs)
                )

    def __add__(self, other) -> CommonLedger:
        """
        Merge two CommonLedger together, and return the newl created ledger.

        Parameters
        ----------
        other : CommonLedger

        Returns
        -------
        CommonLedger
        """
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
                            get_done_msgs=get_done_msgs,
                            select_deselect_msgs=select_deselect_msgs)

    def __iadd__(self, other: CommonLedger):
        """
        Overrides the plus equal operator (+=).

        Parameters
        ----------
        other : CommonLedger

        Returns
        -------
        CommonLedger
        """
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
        """
        Translate the object to a json represenation in bytes.
        Uset to send the object over a network connection.

        Returns
        -------
        bytes
            json representation of the object.
        """

        self.remove_old()
        data = {}
        data['type'] = 'CommonLedger'
        data['NUMBER_OF_FLOORS'] = self.NUMBER_OF_FLOORS
        data['_get_done_msgs'] = self._get_done_msgs.tolist()
        data['_select_msgs'] = self._select_msgs.tolist()
        return json.dumps(data).encode()

    def add_task_get(self, floor, ud, timestamp=None):
        """
        Add a new get task, if it is less informative than the old one, \
        nothing will happen.
        """
        # up: 0 down: 1
        if timestamp is None:
            timestamp = now()
        assert floor <= self.NUMBER_OF_FLOORS
        merge_in_get(self._get_done_msgs[floor, ud, :], timestamp)

    def add_task_done(self, floor, ud, timestamp=None):
        """
        Add a new done message, if it is less informative than the old one, \
        nothing will happen.
        """
        # up: 0 down: 1
        if timestamp is None:
            timestamp = now()
        assert floor <= self.NUMBER_OF_FLOORS
        merge_in_done(self._get_done_msgs[floor, ud, :], timestamp)

    def add_select(self, floor, ud, etd, id,  timestamp=None):
        """
        Add a new select message, if it is less informative than the old one, \
        nothing will happen.
        """
        if timestamp is None:
            timestamp = now()
        select = np.array([timestamp, etd, id], dtype=np.int64)
        merge_in_select(self._select_msgs[floor, ud, :], select)

    def remove_old(self):
        """
        Removes all select messages that are older than SELECT_TIMEOUT
        """
        old = now() - self._select_msgs[:, :, STAMP] > SELECT_TIMEOUT
        self._select_msgs[np.where(old)] = (0, 0, 0)

    @property
    def jobs(self):
        """
        Returns an array representation of all the get tasks. For every floor\
        and direction it return 0 if there is no task or the timestamp of the\
        request if there is one.
        """
        has_task = (self._get_done_msgs[:, :, GET]
                    > self._get_done_msgs[:, :, DONE])
        return np.where(has_task,
                        self._get_done_msgs[:, :, GET],
                        0)

    @property
    def available_jobs(self):
        """
        Returns an array representation of all the get tasks that are not\
        selected. For every floor and direction it return 0 if there is no\
        task or the timestamp of the request if there is one.
        """
        has_task = (self._get_done_msgs[:, :, GET]
                    > self._get_done_msgs[:, :, DONE])
        self.remove_old()
        not_selected = self._select_msgs[:, :, STAMP] == 0

        return np.where(has_task * not_selected,
                        self._get_done_msgs[:, :, GET],
                        0)

    def get_selected_jobs(self, id):
        """
        Returns an array representation of all the get tasks that are selected\
        bu the id. For every floor and direction it return 0 if there is no\
        task or the timestamp of the request if there is one.
        """
        has_task = (self._get_done_msgs[:, :, GET]
                    > self._get_done_msgs[:, :, DONE])
        # where the select timestamp is greater than deselect timestamp
        self.remove_old()
        valid_id = self._select_msgs[:, :, ID] == id

        return np.where(has_task * valid_id,
                        self._get_done_msgs[:, :, GET],
                        0)

    def remove_selection(self, floor, direction, id):
        """
        Removes all select messages matching id.
        """
        if id == self._select_msgs[floor, direction, ID]:
            self._select_msgs[floor, direction, :] = (0, 0, 0)


if __name__ == '__main__':
    """
    Run this too to see how some of the functions works.
    """
    a = CommonLedger(4)
    id1 = 100
    a.add_task_get(1, 0)
    a.add_select(1, 0, now() + 5e6, id1)

    b = CommonLedger(4)
    id2 = 200
    b.add_task_get(2, 1)
    b.add_select(1, 0, now() + 2e6, id2)
    c = a + b

    d = CommonLedger(json_data=c.encode())
    print(c)
    print('D == A + B: ', c == a+b)
