#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Feb 17 14:18:30 2020

@author: user_id
"""


import udp as udp
import asyncio
import time
import logging
from ledger_common import CommonLedger
from typing import Optional

class NetworkLink:
    """
    Object used to communicate between the elevator. It uses udp to broadcast
    its local CommonLedger over the local network to the other elevators,
    and merges other CommonLedgers into its own CommonLedgers.
    """
    def __init__(self,
                 port: int,
                 common_ledger: CommonLedger,
                 queue_size: int = 100,
                 update_rate: int = 1,
                 sendto: list or int = None):
        """
        Parameters
        ----------
        port : int
            Port to listen to.

        common_ledger : CommonLedger

        queue_size : int, optional
            Size of the udp queue. The default is 100.

        update_rate : int, optional
            Number of broadcasts per second. The default is 1.

        sendto : list or int, optional
            The port to broadcast to. On linux multiple programs can listen to
            the same port, but on windows different ports are required.
            The default is None.

        Returns
        -------
        None.

        """


        self.port = port
        self.queue_size = queue_size
        self.loop_time = 1/update_rate
        self.common_ledger = common_ledger
        self.id = hash(time.time())
        if sendto is None:
            self.sendto = [port]
        else:
            self.sendto = sendto

        self.endpoint = None
        # self.out_ip = '255.255.255.255'
        self.out_ip = 'localhost'
        self.out_addr = ('localhost', port)

    async def __aenter__(self):
        """
        Open the connection
        """
        initial_port = self.port
        while 1:
            try:
                assert self.port <= initial_port + 5
                self.endpoint = await udp.open_endpoint(
                    port=self.port, queue_size=self.queue_size)
                return self
            except OSError:
                self.port += 1

    async def __aexit__(self, exc_type, exc, tb):
        """
        Close the connection
        """
        self.endpoint.close()

    async def broadcast(self, data: bytes):
        """
       Broadcast the data.

        Parameters
        ----------
        data : bytes
            Data to broadcast.
        """

        for port in self.sendto:
            self.endpoint.send(data, (self.out_ip, port))

    def queie_is_empty(self):
        """
        Test if there are any new messages in the queue.
        """
        return self.endpoint.que_is_empty()

    async def pop(self):
        """
        Pop the first message in the queue.
        """
        data, addr = await self.endpoint.receive()
        return data, addr

    async def run(self):
        """
        Main function to run the class asyncronously.
        """

        while 1:
            start_time = time.time()
            while not self.endpoint.que_is_empty():
                data, addr = await self.pop()
                id_bytes = data[:8]
                json_data = data[8:]
                if int.from_bytes(id_bytes, 'big') != self.id:
                    self.common_ledger += json_data
            bytes_out = ((self.id).to_bytes(8, 'big')
                         + self.common_ledger.encode())
            await self.broadcast(bytes_out)

            delta = time.time() - start_time
            if self.loop_time < delta:
                logging.warning('Not enough time to finish')

            await asyncio.sleep(max(0, self.loop_time - delta))
