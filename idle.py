#!/usr/bin/env python

import socket
import struct

name = socket.gethostname()
response_msg = name.encode('utf-8')
query_msg = b"Anybody out there?"

multicast_ttl = 1
multicast_group = '224.1.1.1'
multicast_port = 5007
buffer_size = 508

# setup multicast writer
writer = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
writer.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, multicast_ttl)

# setup multicast reader
reader = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
reader.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
reader.bind((multicast_group, multicast_port))
mreq = struct.pack("4sl", socket.inet_aton(multicast_group), socket.INADDR_ANY)
reader.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

def idle():
  while True:
    data = reader.recv(buffer_size)
    if data == query_msg:
      writer.sendto(response_msg, (multicast_group, multicast_port))

try:
  idle()
except KeyboardInterrupt:
  pass
