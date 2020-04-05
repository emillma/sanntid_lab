# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 16:15:09 2020

waiting for error fix in Numba
https://github.com/numba/numba/issues/5100
@author: user_id
"""

from __future__ import annotations
import numpy as np
from utils import toclock, now
import json
from typing import Optional


def merge_in_deliver(deliver_done: np.array, new_timestamp: int = 1e6):
    """
    Function used to merge in a new deliver task.

    Parameters
    ----------
    deliver_done : TYPE
        The old deliver done array. [deliver, done]
    new_timestamp : TYPE, optional
        The timestamp of the new merge task. The default is 1e6.

    Returns
    -------
    None.

    """

    if not deliver_done[0]:
        deliver_done[0] = new_timestamp
    # If the old message is invalid
    elif deliver_done[0] < deliver_done[1]:
        if new_timestamp > deliver_done[1]:
            deliver_done[0] = new_timestamp
        else:
            deliver_done[0] = np.minimum(deliver_done[0], new_timestamp)
    # If the old message is valid
    else:
        deliver_done[0] = np.minimum(deliver_done[0], new_timestamp)


def merge_in_done(get_done: np.array, new_timestamp: int = 1e6):
    """
    Function used to merge in anew done message.

    Parameters
    ----------
    get_done : np.array
        The old deliver done array. [deliver, done]

    new_timestamp : int, optional
        The timestamp of the done message. The default is 1e6.

    Returns
    -------
    None.

    """

    get_done[1] = np.maximum(get_done[1], new_timestamp)


class LocalLedger:
    """
    Class used to keep track off all tasks that are elevator spesific.

    Works in a similar way as the Set data type where the most relevant task
    is kept track of when using the '+' or "+=" operators.
    """

    def __init__(self, number_of_floors: int = None,
                 deliver_done_msgs: Optional[np.array] = None,
                 stop_continue_msgs: Optional[np.array] = None,
                 block_deblock_msgs: Optional[np.array] = None,
                 json_data: Optional[bytes] = None):
        """
        Initialise the ledger.
        If json_data is not None, it will be decoded and used to initialize \
        the object.

        Parameters
        ----------
        number_of_floors : int, optional
            Number of floors supported. The default is None.

        deliver_done_msgs : Optional[np.array], optional
            Array representing the deliver done messages. The default is None.

        stop_continue_msgs : Optional[np.array], optional
            Array representing the block deblock messages. The default is None.

        block_deblock_msgs : Optional[np.array], optional
            DESCRIPTION. The default is None.

        json_data : Optional[bytes], optional
            DESCRIPTION. The default is None.

        Returns
        -------
        None.

        """


        # floor, get/done
        if json_data:
            data = json.loads(json_data.decode())
            assert data['type'] == 'LocalLedger', TypeError
            self.NUMBER_OF_FLOORS = data['NUMBER_OF_FLOORS']
            self.deliver_done_msgs = np.array(data['deliver_done_msgs'],
                                              dtype=np.int64)
            self.stop_continue_msgs = np.array(data['stop_continue_msgs'],
                                               dtype=np.int64)
            self.block_deblock_msgs = np.array(data['block_deblock_msgs'],
                                               dtype=np.int64)

        else:
            assert number_of_floors
            self.NUMBER_OF_FLOORS = number_of_floors

            if not np.any(deliver_done_msgs):
                self.deliver_done_msgs = np.zeros((number_of_floors, 2),
                                                  dtype=np.int64)
            else:
                self.deliver_done_msgs = deliver_done_msgs

            # stop/continue
            if not np.any(stop_continue_msgs):
                self.stop_continue_msgs = np.zeros((2), dtype=np.int64)
            else:
                self.stop_continue_msgs = stop_continue_msgs

            # block_deblock_msgs/block_deblock_msgs
            if not np.any(stop_continue_msgs):
                self.block_deblock_msgs = np.zeros((2), dtype=np.int64)
            else:
                self.block_deblock_msgs = block_deblock_msgs

    def __repr__(self) -> str:
        """
        Returns
        -------
        str
            Readable representation of the ledger.
        """

        out = 'Deliver Done Messages\n'
        for floor in range(self.deliver_done_msgs.shape[0]):
            out += f'Floor {floor:2d}:    '
            time_get = toclock(self.deliver_done_msgs[floor, 0])
            time_done = toclock(self.deliver_done_msgs[floor, 1])
            out += f'DELIVER: {time_get}    DONE: {time_done}'
            out += '\n'
        out += '\n'

        time_stop = toclock(self.stop_continue_msgs[0])
        time_continue = toclock(self.stop_continue_msgs[1])
        out += 'Stop Continue Messages\n'
        out += f'Stop: {time_stop}     Continue: {time_continue}\n\n'

        time_block = toclock(self.block_deblock_msgs[0])
        time_deblock = toclock(self.block_deblock_msgs[1])
        out += 'Block Deblock Messages\n'
        out += f'Stop: {time_block}     Continue: {time_deblock}'
        return out

    def __str__(self) -> str:
        """
        Returns
        -------
        str
            Readable representation of the ledger.
        """

        return self.__repr__()

    def __eq__(self, other: LocalLedger) -> bool:
        """
        Test if two local ledgers are equal.

        Parameters
        ----------
        other : LocalLedger

        Returns
        -------
        bool
            True if their data is the same, else False.

        """

        assert isinstance(other, LocalLedger)
        return (np.array_equal(self.deliver_done_msgs,
                               other.deliver_done_msgs) and
                np.array_equal(self.stop_continue_msgs,
                               other.stop_continue_msgs) and
                np.array_equal(self.block_deblock_msgs,
                               other.block_deblock_msgs)
                )

    def __add__(self, other: LocalLedger) -> LocalLedger:
        """
        Merge two local ledgers together, and return the newl created ledger.

        Parameters
        ----------
        other : LocalLedger

        Returns
        -------
        LocalLedger
        """

        assert isinstance(other, LocalLedger)
        deliver_done_msgs = self.deliver_done_msgs.copy()
        stop_continue_msgs = self.stop_continue_msgs.copy()
        block_deblock_msgs = self.block_deblock_msgs.copy()
        for floor in range(self.NUMBER_OF_FLOORS):

            merge_in_deliver(deliver_done_msgs[floor, :],
                             other.deliver_done_msgs[floor, 0])

            merge_in_done(deliver_done_msgs[floor, :],
                          other.deliver_done_msgs[floor, 1])

        stop_continue_msgs = np.maximum(stop_continue_msgs,
                                        other.stop_continue_msgs)

        block_deblock_msgs = np.maximum(block_deblock_msgs,
                                        other.block_deblock_msgs)

        return LocalLedger(self.NUMBER_OF_FLOORS, deliver_done_msgs,
                           stop_continue_msgs, block_deblock_msgs)

    def __iadd__(self, other: LocalLedger) -> LocalLedger:
        """
        Parameters
        ----------
        other : LocalLedger
            DESCRIPTION.

        Returns
        -------
        LocalLedger
        """

        if isinstance(other, bytes):
            other = LocalLedger(json_data=other)
        assert isinstance(other, LocalLedger)

        for floor in range(self.NUMBER_OF_FLOORS):

            merge_in_deliver(self.deliver_done_msgs[floor, :],
                             other.deliver_done_msgs[floor, 0])

            merge_in_done(self.deliver_done_msgs[floor, :],
                          other.deliver_done_msgs[floor, 1])

        self.stop_continue_msgs = np.maximum(self.stop_continue_msgs,
                                             other.stop_continue_msgs)

        self.block_deblock_msgs = np.maximum(self.block_deblock_msgs,
                                             other.block_deblock_msgs)

        return self

    def encode(self) -> bytes:
        """
        Translate the object to a json represenation in bytes.
        Uset to send the object over a network connection.

        Returns
        -------
        bytes
            json representation of the object.
        """

        data = {}
        data['type'] = 'LocalLedger'
        data['NUMBER_OF_FLOORS'] = self.NUMBER_OF_FLOORS
        data['deliver_done_msgs'] = self.deliver_done_msgs.tolist()
        data['stop_continue_msgs'] = self.stop_continue_msgs.tolist()
        data['block_deblock_msgs'] = self.block_deblock_msgs.tolist()
        return json.dumps(data).encode()

    def add_task_deliver(self, floor, timestamp=None):
        # up: 0 down: 1
        if timestamp is None:
            timestamp = now()
        merge_in_deliver(self.deliver_done_msgs[floor, :], timestamp)

    def add_task_done(self, floor, timestamp=None):
        # up: 0 down: 1
        if timestamp is None:
            timestamp = now()
        merge_in_done(self.deliver_done_msgs[floor, :], timestamp)

    def add_stop(self, timestamp=None):
        if timestamp is None:
            timestamp = now()
        self.stop_continue_msgs[0] = np.maximum(self.stop_continue_msgs[0],
                                                timestamp)

    def add_continue(self, timestamp=None):
        if timestamp is None:
            timestamp = now()
        self.stop_continue_msgs[1] = np.maximum(self.stop_continue_msgs[1],
                                                timestamp)

    def add_block(self, timestamp=None):
        if timestamp is None:
            timestamp = now()
        self.block_deblock_msgs[0] = np.maximum(self.stop_continue_msgs[0],
                                                timestamp)

    def add_deblock(self, timestamp=None):
        if timestamp is None:
            timestamp = now()
        self.block_deblock_msgs[1] = np.maximum(self.stop_continue_msgs[1],
                                                timestamp)

    def get_deliver(self):
        return self.deliver_done_msgs[:, 0] > self.deliver_done_msgs[:, 1]

    def get_stop(self):
        return self.stop_continue_msgs[0] > self.stop_continue_msgs[1]

    def get_block(self):
        return self.block_deblock_msgs[0] > self.block_deblock_msgs[1]

if __name__ == '__main__':
    a = LocalLedger(4)
    b = LocalLedger(4)
    b.add_task_done(1, now())
    a.add_task_done(1, now())
    a.add_task_deliver(1, now() + 1)
    b.add_task_deliver(1, now() + 1)
    a.add_stop(now())
    c = a + b
