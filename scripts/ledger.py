# -*- coding: utf-8 -*-
"""
Created on Mon Feb 24 16:15:09 2020

waiting for error fix in Numba
https://github.com/numba/numba/issues/5100
@author: user_id
"""

from __future__ import annotations
import numpy as np
import numba as nb
import time

def regular_merge(a, b, select_func):
    assert a.shape == b.shape
    out = np.empty(a.shape, dtype=a.dtype)
    and_args = np.where(np.logical_and(a, b))
    xor_args = np.where(np.logical_xor(a, b))
    out[and_args] = select_func(a[and_args], b[and_args])
    out[xor_args] = np.where(a[xor_args], a[xor_args], b[xor_args])
    return out

@nb.njit(nb.int64[:, :, :, ::1](nb.int64[:, :, :, ::1],
                                nb.int64[:, :, :, ::1],
                                nb.int64),
         cache = True)
def select_msgs_merge(a, b, limit):
    assert a.shape == b.shape
    out = a.copy()

    # For every floor
    for i in nb.prange(a.shape[0]):
        # For up and down selections
        for j in nb.prange(a.shape[1]):

            # If only one os valid
            if bool(a[i, j, 0, 0]) != bool(b[i, j, 0, 0]):
                # A is default, so if it is b, swap
                if bool(b[i, j, 0, 0]):
                    out[i, j, 0, :] = b[i, j, 0, :]

            # If both are valid
            elif a[i, j, 0, 0] and b[i, j, 0, 0]:
                #If the timestamps are similar
                if (abs(a[i, j, 0, 0] - b[i, j, 0, 0]) < limit):
                    # If the ETD of a is larger than b, swap
                    if (a[i, j, 0, 1]) > b[i, j, 0, 1]:
                        out[i, j, 0, :] = b[i, j, 0, :]
                else:
                    # If the timestamp of a is smaller
                    if (a[i, j, 0, 0]) < b[i, j, 0, 0]:
                        out[i, j, 0, :] = b[i, j, 0, :]

            """
            After adding the correct select message,
            find the deselct with most information (share id)
            """
            # If only one os valid
            if (bool(a[i, j, 1, 0]) != bool(b[i, j, 1, 0])):
                if (bool(b[i, j, 1, 0])):
                    out[i, j, 1, :] = b[i, j, 1, :]

            # If both are valid
            elif (a[i, j, 1, 0] and b[i, j, 1, 0]):
                # If only one has mathcing ID to current select
                if ((a[i, j, 1, 2] == out[i, j, 0, 2])
                        != (a[i, j, 1, 2] == out[i, j, 0, 2])):
                    if b[i, j, 1, 2] == out[i, j, 0, 2]:
                        out[i, j, 1, :] = b[i, j, 1, :]
                else:
                    if a[i, j, 1, 0] > b[i, j, 1, 0]:
                        out[i, j, 1, :] = b[i, j, 1, :]
    return out


class Ledger:

    def __init__(self, number_of_floors):
        self.NUMBER_OF_FLOORS = number_of_floors
        self.data = {}

    def merge(self, other):
        pass

    def __add__(self, other: Ledger):
        if type(self) == type(other):
            return self.merge(other)
        else:
            raise TypeError(f'Cannot add {self.ledger_type} and type(other)')


class CommonLedger(Ledger):

    def __init__(self, number_of_floors):
        super().__init__(number_of_floors)
        # floor, up/down, get/done
        self.get_done_msgs = np.zeros((number_of_floors, 2, 2),
                                      dtype=np.int64)
        # floor, up/down, select/deselect, stamp/etd/id
        self.select_deselect_msgs = np.zeros((number_of_floors, 2, 2, 3),
                                             dtype=np.int64)


    def merge(self, other):
        out = {}
        get_done_msgs = np.empty(self.get_done_msgs.shape, np.float64)
        get_done_msgs[:, :, 0] = regular_merge(self.get_done_msgs[:, :, 0],
                                               other.get_done_msgs[:, :, 0],
                                               np.minimum)
        get_done_msgs[:, :, 1] = regular_merge(self.get_done_msgs[:, :, 1],
                                               other.get_done_msgs[:, :, 1],
                                               np.maximum)

        select_deselect_msgs = select_msgs_merge(self.select_deselect_msgs,
                                                 other.select_deselect_msgs)


a = CommonLedger(19)

a = (np.random.random((50000,2,2))*10000).astype(np.int64)
# a[0,:,:,:] = 0
b = (np.random.random((50000,2,2))*10000).astype(np.int64)
t = time.time()
out = regular_merge(a,b, np.maximum)
stop = time.time() - t
print(stop)


