#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Feb 11 16:18:13 2020

@author: emil


Provide high-level UDP endpoints for asyncio.
Example:
async def main():
    # Create a local UDP enpoint
    local = await open_local_endpoint('localhost', 8888)
    # Create a remote UDP enpoint, pointing to the first one
    remote = await open_remote_endpoint(*local.address)
    # The remote endpoint sends a datagram
    remote.send(b'Hey Hey, My My')
    # The local endpoint receives the datagram, along with the address
    data, address = await local.receive()
    # This prints: Got 'Hey Hey, My My' from 127.0.0.1 port 8888
    print(f"Got {data!r} from {address[0]} port {address[1]}")
"""
import asyncio
import socket
import logging


class DatagramEndpointProtocol(asyncio.DatagramProtocol):
    """Datagram protocol for the endpoint high-level interface."""

    def __init__(self, endpoint):
        self._endpoint = endpoint

    # Protocol methods

    def connection_made(self, transport: asyncio.transports.DatagramTransport):
        self._endpoint._transport = transport

        sock = transport.get_extra_info("socket")  # type: socket.socket
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)

    def connection_lost(self, exc):
        if exc is not None:  # pragma: no cover
            msg = 'Endpoint lost the connection: {!r}'
            logging.warning(msg.format(exc))
        self._endpoint.close()

    # Datagram protocol methods

    def datagram_received(self, data, addr):
        self._endpoint.feed_datagram(data, addr)

    def error_received(self, exc):
        msg = 'Endpoint received an error: {!r}'
        logging.warning(msg.format(exc))


# Enpoint classes

class Endpoint:
    """High-level interface for UDP enpoints.
    Can either be local or remote.
    It is initialized with an optional queue size for the incoming datagrams.
    """

    def __init__(self, queue_size=None):
        if queue_size is None:
            queue_size = 0
        self._queue = asyncio.Queue(queue_size)
        self._closed = False
        self._transport = None

    # Protocol callbacks

    def feed_datagram(self, data, addr):
        try:
            self._queue.put_nowait((data, addr))
        except asyncio.QueueFull:
            logging.warning('Endpoint queue is full')

    def close(self):
        # Manage flag
        if self._closed:
            return
        self._closed = True
        # Wake up
        if self._queue.empty():
            self.feed_datagram(None, None)
        # Close transport
        if self._transport:
            self._transport.close()

    # User methods

    def send(self, data, addr):
        """Send a datagram to the given address."""
        if self._closed:
            raise IOError("Enpoint is closed")
        self._transport.sendto(data, addr)

    async def receive(self):
        """Wait for an incoming datagram and return it with
        the corresponding address.
        This method is a coroutine.
        """
        if self._queue.empty() and self._closed:
            raise IOError("Enpoint is closed")
        data, addr = await self._queue.get()
        if data is None:
            raise IOError("Enpoint is closed")
        return data, addr

    def abort(self):
        """Close the transport immediately."""
        if self._closed:
            raise IOError("Enpoint is closed")
        self._transport.abort()
        self.close()

    def que_is_empty(self):
        return self._queue.empty()

    # Properties

    @property
    def address(self):
        """The endpoint address as a (host, port) tuple."""
        return self._transport.get_extra_info("socket").getsockname()

    @property
    def closed(self):
        """Indicates whether the endpoint is closed or not."""
        return self._closed


async def open_endpoint(
        host='0.0.0.0', port=0, *, queue_size=None, **kwargs):
    loop = asyncio.get_event_loop()
    endpoint = Endpoint(queue_size)
    await loop.create_datagram_endpoint(
        protocol_factory=lambda: DatagramEndpointProtocol(endpoint),
        local_addr=(host, port))
    return endpoint
