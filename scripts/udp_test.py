#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 12 17:03:43 2020

@author: emil
"""


import udp
import asyncio

async def main():
    # Create a local UDP enpoint
    local_list = []
    for i in range(2):
        local_list.append(await udp.open_local_endpoint('localhost', 9000))
    # Create a remote UDP enpoint, pointing to the first one
    remote = await udp.open_remote_endpoint(*local_list[0].address)
    # The remote endpoint sends a datagram
    remote.send(b'Hey Hey, My My')
    # The local endpoint receives the datagram, along with the address
    for local in local_list:
        data, address = await local.receive()
        # This prints: Got 'Hey Hey, My My' from 127.0.0.1 port 8888
        print(f"Got {data!r} from {address[0]} port {address[1]}")
    
asyncio.run(main())