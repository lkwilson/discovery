#!/usr/bin/env python

import threading
import time
import socket
import struct

query_msg = b"Anybody out there?"

query_interval = 0.5
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

def handle_peer_msgs():
  peers = set()
  while True:
    data, (peer_ip, peer_port) = reader.recvfrom(buffer_size)
    if data == query_msg:
      continue
    hostname = data.decode('utf-8')
    key = (hostname, peer_ip)
    if key in peers:
      continue
    print('peer:', hostname, peer_ip)
    peers.add(key)

def send_query_msgs():
  while True:
    writer.sendto(query_msg, (multicast_group, multicast_port))
    time.sleep(query_interval)

def main():
  read_thread = threading.Thread(target=handle_peer_msgs)
  read_thread.start()

  write_thread = threading.Thread(target=send_query_msgs)
  write_thread.start()

  read_thread.join()
  print('hi')
  write_thread.join()

try:
  main()
except KeyboardInterrupt:
  pass
