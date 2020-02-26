#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 19:12:42 2020

@author: emil
"""


def toclock(time, factor = 1e6):
    if time:
        return datetime.datetime.fromtimestamp(time / factor).strftime(
            "%H:%M:%S.%f")
    else:
        return str(None) + ' '*11