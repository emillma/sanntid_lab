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


def merge_in_deliver(deliver_done, new_timestamp=1e6):
    if not deliver_done[0]:
        deliver_done[0] = new_timestamp
    # If the old message is invalid
    elif deliver_done[0] < deliver_done[1]:
        if new_timestamp > deliver_done[1]:
            deliver_done[0] = new_timestamp
    # If the old message is valid
    else:
        # If the new message also is valid
        if new_timestamp > deliver_done[1]:
            deliver_done[0] = np.minimum(deliver_done[0], new_timestamp)


def merge_in_done(get_done, new_timestamp=1e6):
    get_done[1] = np.maximum(get_done[1], new_timestamp)


class LocalLedger:

    def __init__(self, number_of_floors,
                 deliver_done_msgs=None, stop_continue_msgs=None,
                 block_deblock_msgs=None):

        self.NUMBER_OF_FLOORS = number_of_floors
        # floor, get/done
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

    def __repr__(self):
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
    def __str__(self):
        return self.__repr__()

    def __eq__(self, other: LocalLedger):
        assert isinstance(other, LocalLedger)
        return (np.array_equal(self.deliver_done_msgs,
                               other.deliver_done_msgs) and
                np.array_equal(self.stop_continue_msgs,
                               other.stop_continue_msgs) and
                np.array_equal(self.block_deblock_msgs,
                               other.block_deblock_msgs)
                )

    def __add__(self, other):
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

    def add_task_deliver(self, floor, timestamp):
        # up: 0 down: 1
        merge_in_deliver(self.deliver_done_msgs[floor, :], timestamp)

    def add_task_done(self, floor, timestamp):
        # up: 0 down: 1
        merge_in_done(self.deliver_done_msgs[floor, :], timestamp)

    def add_stop(self, timestamp):
        self.stop_continue_msgs[0] = np.maximum(self.stop_continue_msgs[0],
                                                timestamp)

    def add_continue(self, timestamp):
        self.stop_continue_msgs[1] = np.maximum(self.stop_continue_msgs[1],
                                                timestamp)

    def add_block(self, timestamp):
        self.stop_continue_msgs[0] = np.maximum(self.stop_continue_msgs[0],
                                                timestamp)

    def add_deblock(self, timestamp):
        self.stop_continue_msgs[1] = np.maximum(self.stop_continue_msgs[1],
                                                timestamp)


if __name__ == '__main__':
    a = LocalLedger(4)
    b = LocalLedger(4)
    a.add_task_deliver(1, stamp())
    b.add_task_deliver(1, stamp())
    b.add_task_done(1, stamp())
    a.add_task_done(1, stamp())
    a.add_stop(stamp())
    c = a + b
