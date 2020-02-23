#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 19 17:51:28 2020

@author: emil
"""
from __future__ import annotations
import json
import bisect
import time
import random


def merge_lists(list_1, list_2, sort_keys: list, choose_func):
    """
    Merge two lists into one. They have to be sorted by the same sort keys.
    The sort keys also defines the uniqueness of an element

    """

    out = []
    short, long = sorted([list_1, list_2], key=lambda x: len(x))
    j = 0
    for i in range(len(long)):
        if j >= len(short):
            out.append(long[i])
            continue

        value_1 = [long[i][key] for key in sort_keys]
        value_2 = [short[j][key] for key in sort_keys]

        if value_1 == value_2:
            out.append(choose_func(long[i], short[j]))
            j += 1

        elif value_1 >= value_2:
            out.append(short[j])
            out.append(long[i])
            j += 1

        else:
            out.append(long[i])
    return out


keys = ['floor', 'timestamp']

l1 = [{'floor': 0, 'd': random.randint(0, 1), 't': random.random()}]
l2 = [{'floor': 0, 'd': random.randint(0, 1), 't': random.random()}]


for i in range(random.randint(5, 10)):
    new = l1[-1].copy()
    new['floor'] += random.randint(1, 3)
    new['t'] = random.random()
    new['d'] = random.randint(0, 1)
    l1.append(new)

for i in range(random.randint(5, 10)):
    new = l2[-1].copy()
    new['floor'] += random.randint(1, 3)
    new['t'] = random.random()
    l2.append(new)


l3 = merge_lists(l1, l2, ['floor', 'd'],
                 lambda a, b: a if a['t'] < b['t'] else b)
