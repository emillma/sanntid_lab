import time
myip = '10.100.23.235'

import socket
BUFFER_SIZE = 1024
UDP_IP = ""
UDP_PORT = 30000

sock_udp = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock_udp.bind((UDP_IP, UDP_PORT))


data, addr = sock_udp.recvfrom(BUFFER_SIZE) # buffer size is 1024 bytes
search = " at "
index = str(data).find(search) + len(search)
TCP_IP = str(data)[index:-2]
print('Tcp ip:', TCP_IP)
time.sleep(0.1)
sock_udp.close()

TCP_PORT = 34933
sock_tcp = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_tcp.connect((TCP_IP, TCP_PORT))
data = sock_tcp.recv(BUFFER_SIZE)
print(str(data))
sock_tcp.close()
