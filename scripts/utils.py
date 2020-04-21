#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 19:12:42 2020.

@author: user_id
"""
import datetime
import time


def toclock(time) -> str:
    """Convert the time to a pretty format.

    Parameters
    ----------
    time : TYPE
        Time as int with micrisecond precision.

    Returns
    -------
    str
        Pressy version of the time, or 'None' if the time is 0.

    """
    if time:
        return datetime.datetime.fromtimestamp(time / 1e6).strftime(
            "%H:%M:%S.%f")
    else:
        return ' ' * 11 + str(None)


def time_to_int(time):
    """Translate time to int representation."""
    return int(round(time * 1e6))


def int_to_time(number):
    """Translate int to time representation."""
    return number / 1e6


def now() -> int:
    """Get the curent tim as int.

    Returns
    -------
    int
        Time as int with macro second precision.

    """
    return int(round(time.time() * 1e6))
