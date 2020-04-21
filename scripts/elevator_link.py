# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 12:07:36 2020

@author: user_id
"""
from __future__ import annotations
from typing import Optional

import asyncio
import logging


class ElevatorLink:
    """Object used to ocmmunicate wit the elevator over TCP."""

    def __init__(self, port=15657, floor_n=4):
        self.TCP_IP = 'localhost'
        self.TCP_PORT = port
        self.BUFFER_SIZE = 1024

        self.NUMBER_OF_FLOORS = floor_n
        self.last_floor = None
        self.reader_lock = asyncio.Lock()
        self.writer_lock = asyncio.Lock()
        self.connection_lock = asyncio.Lock()
        self.every = 0.1
        self.connected = False

    async def connect(self) -> Optional[Exception]:
        """Connect to elevator port.

        Funtion used to open a TCP connection with the elevator.

        Returns
        -------
        Optional[Exception]
            Error if communication with elevator is broken.

        """
        async with self.connection_lock:
            logging.info('Trying to connect')
            try:
                self.reader, self.writer = await asyncio.open_connection(
                    self.TCP_IP, self.TCP_PORT)
                self.connected = True
                logging.info(f'{self} connected to elevator')
            except OSError as error:
                logging.info(f'{self} connection failed')
                logging.warning(error)
                self.connected = False

    async def __aenter__(self):
        """Open connection."""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """Close connection."""
        if self.connected:
            async with self.writer_lock:
                self.writer.close()
                await self.writer.wait_closed()

    async def _elev_tell(self, command: str) -> Optional[Exception]:
        """Send data to elevator.

        Returns
        -------
        Optional[Exception]
            Error if communication with elevator is broken.

        """
        try:
            assert self.connected, f'{self} is not connected'
            async with self.writer_lock:
                self.writer.write(bytearray.fromhex(command))
                await self.writer.drain()

        except (ConnectionResetError, AssertionError) as error:
            logging.warning(error)
            self.connected = False
            if not self.connection_lock.locked():
                await self.connect()
            return error

    async def _elev_get(self, command: str) -> (Optional[Exception], bytes):
        """Get data from elevator.

        Returns
        -------
         (Optional[Exception], Optional[bytes])
            Error if communication with elevator is broken.
            Data

        """
        retval = await self._elev_tell(command)
        if retval:
            return retval, None
        else:
            try:
                async with self.reader_lock:
                    return None, await self.reader.read(4)

            except ConnectionResetError as error:
                logging.error(error)
                return error, None
                self.connected = False
                await self.connect()

    async def stop(self) -> Optional[Exception]:
        """Tell the elevator to stop.

        Returns
        -------
        Optional[Exception]
            Error if communication with elevator is broken.

        """
        return await self._elev_tell('01000000')

    async def go_up(self) -> Optional[Exception]:
        """Tell the elevator to go up.

        Returns
        -------
        Optional[Exception]
            Error if communication with elevator is broken.

        """
        return await self._elev_tell('01010000')

    async def go_down(self) -> Optional[Exception]:
        """
        Tell the elevator to go down.

        Returns
        -------
        Optional[Exception]
            Error if communication with elevator is broken.

        """
        return await self._elev_tell('01ff0000')

    async def set_button_light(self, floor: int,
                               button: int, value: int) -> Optional[Exception]:
        """Set a button light.

        Parameters
        ----------
        floor : int

        button : int
            0: up, 1: down, 2, cab.
        value : int
            on: 1, off: 0.

        Returns
        -------
        Optional[Exception]
            Error if communication with elevator is broken.

        """
        return await self._elev_tell(f'02{button:02x}{floor:02x}{value:02x}')

    async def set_floor_indicator(self, floor: int) -> Optional[Exception]:
        """Set floor indicator.

        The light at all other floors wil automatically turn off.

        Parameters
        ----------
        floor : int

        Returns
        -------
        Optional[Exception]
            Error if communication with elevator is broken.

        """
        return await self._elev_tell(f'03{floor:02x}0000')

    async def set_door_light(self, value: int) -> Optional[Exception]:
        """Turn the door light on or off.

        Parameters
        ----------
        value : int
            1 to turn on, 0 to turn off.

        Returns
        -------
        Optional[Exception]
            Error if communication with elevator is broken.
        """
        return await self._elev_tell(f'04{value:02x}0000')

    async def set_stop_light(self, value: int) -> Optional[Exception]:
        """Turn the stop ligh on or off.

        Parameters
        ----------
        value : int
            1 to turn on, 0 to turn off.

        Returns
        -------
        Optional[Exception]
            Error if communication with elevator is broken.
        """
        return await self._elev_tell(f'05{value:02x}0000')

    async def get_order_button(self,
                               floor: int,
                               button: int
                               ) -> (Optional[Exception], int):
        """Test if selected order button is pressed.

        Parameters
        ----------
        floor : int
        button : int
            0: up, 1: down, 2, cab.

        Returns
        -------
        (Optional[Exception], int)
            Error if communication with elevator is broken.

        """
        retval, data = await self._elev_get(f'06{button:02x}{floor:02x}00')
        return (retval, data[1]) if not retval else (retval, None)

    async def get_floor(self) -> (Optional[Exception], Optional[int]):
        """Get data from the floor sensors.

        None if elevator is between floors

        Returns
        -------
        (Optional[Exception], Optional[int])
            Error if communication with elevator is broken.
            Floor number if elevator is at a flor, else None.

        """
        retval, data = await self._elev_get('07000000')
        if not retval:
            at_floor = data[1]
            floor = data[2]
            return (retval, floor) if at_floor else (retval, None)
        else:
            return retval, None

    async def get_stop_button(self) -> (Optional[Exception], Optional[int]):
        """Check if the stop button is pressed.

        Returns
        -------
        (Optional[Exception], Optional[int])
            Error if communication with elevator is broken.
            1 if pressed, else 0
        """
        retval, data = await self._elev_get('08000000')
        return (retval, data[1]) if not retval else (retval, None)

    async def get_obstruction_switch(self) -> (Optional[Exception],
                                               Optional[int]):
        """Check if obstuction switch is on.

        Returns
        -------
        (Optional[Exception], Optional[int])
            Error if communication with elevator is broken..
             1 if obstruction, else 0
        """
        retval, data = await self._elev_get('09000000')
        return (retval, data[1]) if not retval else (retval, None)

    @property
    def floor_n(self):
        """Return number of floors."""
        return self.NUMBER_OF_FLOORS
