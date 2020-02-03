# -*- coding: utf-8 -*-
"""
Created on Mon Feb  3 14:05:40 2020

@author: user_id
"""
import socket
import time

TCP_IP = 'localhost'
TCP_PORT = 15657
BUFFER_SIZE = 1024
MESSAGE = meg = bytearray.fromhex('01010000')

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((TCP_IP, TCP_PORT))
s.send(MESSAGE)
data = s.recv(BUFFER_SIZE)
s.close()

print("received data:", data)