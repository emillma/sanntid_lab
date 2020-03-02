#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 19:12:42 2020

@author: emil
"""
import datetime
import time


def toclock(time, factor=1e6):
    if time:
        return datetime.datetime.fromtimestamp(time / factor).strftime(
            "%H:%M:%S.%f")
    else:
        return ' ' * 11 + str(None)


def now():
    return int(round(time.time() * 1e6))


def stamp():
    return int(round(time.time() * 1e6))
