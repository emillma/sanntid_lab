# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 16:15:09 2020.

@author: user_id
"""

from __future__ import annotations
from typing import Optional

import numpy as np
import json

from utils import toclock, now

DELIVER = 0
DONE = 1

BLOCK = 0
UNBLOCK = 1

STOP = 0
CONTINUE = 1


def merge_in_deliver(deliver_done: np.array, new_timestamp: int = 1e6):
    """Merge in a new deliver task.

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
    if not deliver_done[DELIVER]:
        deliver_done[DELIVER] = new_timestamp
    # If the old message is invalid
    elif deliver_done[DELIVER] < deliver_done[DONE]:
        if new_timestamp > deliver_done[DONE]:
            deliver_done[DELIVER] = new_timestamp
        else:
            deliver_done[DELIVER] = np.minimum(deliver_done[DELIVER],
                                               new_timestamp)
    # If the old message is valid
    else:
        deliver_done[DELIVER] = np.minimum(deliver_done[DELIVER],
                                           new_timestamp)


def merge_in_done(deliver_done: np.array, new_timestamp: int = 1e6):
    """Merge in anew done message.

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
    deliver_done[DONE] = np.maximum(deliver_done[DELIVER], new_timestamp)


class LocalLedger:
    """Class used to keep track off all tasks that are elevator spesific.

    AKA all the deliver requests. These requests are referred to as 'deliver'
    tasks.
    They are represented by a timestamp when the DELIVER was requested and a
    timestamp when a request was compleated (DONE).


    It also tracks the STOP button and the obstruction in a similar way.

    Works in a similar way as the 'Set' data type where the most relevant task
    is kept track of when using the '+' or "+=" operators.
    """

    def __init__(self, number_of_floors: int = None,
                 deliver_done_msgs: Optional[np.array] = None,
                 stop_continue_msgs: Optional[np.array] = None,
                 block_deblock_msgs: Optional[np.array] = None,
                 json_data: Optional[bytes] = None) -> LocalLedger:
        """Initialize the ledger.

        If json_data is not None, it will be decoded and used to initialize
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
            A json representation of a LocalLedger object.
            The default is None.
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
        """Return representatnio of ledger.

        Returns
        -------
        str
            Readable representation of the ledger.
        """
        out = 'Deliver Done Messages\n'
        for floor in range(self.deliver_done_msgs.shape[0]):
            out += f'Floor {floor:2d}:    '
            time_get = toclock(self.deliver_done_msgs[floor, DELIVER])
            time_done = toclock(self.deliver_done_msgs[floor, DONE])
            out += f'DELIVER: {time_get}    DONE: {time_done}'
            out += '\n'
        out += '\n'

        time_stop = toclock(self.stop_continue_msgs[DELIVER])
        time_continue = toclock(self.stop_continue_msgs[DONE])
        out += 'Stop Continue Messages\n'
        out += f'Stop: {time_stop}     Continue: {time_continue}\n\n'

        time_block = toclock(self.block_deblock_msgs[DELIVER])
        time_deblock = toclock(self.block_deblock_msgs[DONE])
        out += 'Block Deblock Messages\n'
        out += f'Stop: {time_block}     Continue: {time_deblock}'
        return out

    def __str__(self) -> str:
        """Return string representatnio of ledger.

        Returns
        -------
        str
            Readable representation of the ledger.
        """
        return self.__repr__()

    def __eq__(self, other: LocalLedger) -> bool:
        """Implement == operator.

        Test if two LocalLedger are equal (==).

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
        """Implement + operator.

        Merge two LocalLedger together, and return the new LocalLedger.

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
                             other.deliver_done_msgs[floor, DELIVER])

            merge_in_done(deliver_done_msgs[floor, :],
                          other.deliver_done_msgs[floor, DONE])

        stop_continue_msgs = np.maximum(stop_continue_msgs,
                                        other.stop_continue_msgs)

        block_deblock_msgs = np.maximum(block_deblock_msgs,
                                        other.block_deblock_msgs)

        return LocalLedger(self.NUMBER_OF_FLOORS, deliver_done_msgs,
                           stop_continue_msgs, block_deblock_msgs)

    def __iadd__(self, other: LocalLedger) -> LocalLedger:
        """Implement += operator.

        Overrides the plus equal operator (+=).

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
                             other.deliver_done_msgs[floor, DELIVER])

            merge_in_done(self.deliver_done_msgs[floor, :],
                          other.deliver_done_msgs[floor, DONE])

        self.stop_continue_msgs = np.maximum(self.stop_continue_msgs,
                                             other.stop_continue_msgs)

        self.block_deblock_msgs = np.maximum(self.block_deblock_msgs,
                                             other.block_deblock_msgs)

        return self

    def encode(self) -> bytes:
        """Encode the ledger to bytes.

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
        """Add a deliver task."""
        # up: 0 down: 1
        if timestamp is None:
            timestamp = now()
        merge_in_deliver(self.deliver_done_msgs[floor, :], timestamp)

    def add_task_done(self, floor, timestamp=None):
        """Add a Done message."""
        # up: 0 down: 1
        if timestamp is None:
            timestamp = now()
        merge_in_done(self.deliver_done_msgs[floor, :], timestamp)

    def add_stop(self, timestamp=None):
        """Add a Stop message."""
        if timestamp is None:
            timestamp = now()
        self.stop_continue_msgs[STOP] = np.maximum(
            self.stop_continue_msgs[STOP], timestamp)

    def add_continue(self, timestamp=None):
        """Add a Continue message."""
        if timestamp is None:
            timestamp = now()
        self.stop_continue_msgs[CONTINUE] = np.maximum(
            self.stop_continue_msgs[CONTINUE], timestamp)

    def add_block(self, timestamp=None):
        """Add a Block message."""
        if timestamp is None:
            timestamp = now()
        self.block_deblock_msgs[BLOCK] = np.maximum(
            self.stop_continue_msgs[UNBLOCK], timestamp)

    def add_deblock(self, timestamp=None):
        """Add a Deblock message."""
        if timestamp is None:
            timestamp = now()
        self.block_deblock_msgs[UNBLOCK] = np.maximum(
            self.stop_continue_msgs[UNBLOCK], timestamp)

    @property
    def tasks(self):
        """Return active deliver tasks."""
        return np.where((self.deliver_done_msgs[:, DELIVER]
                         > self.deliver_done_msgs[:, DONE]).ravel(),
                        self.deliver_done_msgs[:, DELIVER],
                        0)

    @property
    def stop(self):
        """Test if stop is pressed."""
        return (self.stop_continue_msgs[STOP]
                > self.stop_continue_msgs[CONTINUE])

    @property
    def block(self):
        """Test if blocked."""
        return (self.block_deblock_msgs[BLOCK]
                > self.block_deblock_msgs[UNBLOCK])


if __name__ == '__main__':
    """Run this too to see how some of the functions works."""
    a = LocalLedger(4)
    b = LocalLedger(4)
    b.add_task_done(1, now())
    a.add_task_done(1, now())
    a.add_task_deliver(1, now() + 1)
    b.add_task_deliver(1, now() + 1)
    a.add_stop(now())
    c = a + b
    d = LocalLedger(json_data=c.encode())
    print(c)
    print('D == A + B: ', c == a+b)
