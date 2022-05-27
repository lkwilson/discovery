#!/usr/bin/env python

import socket
import struct

'''
a framework for sending probes and collecting response information.
'''

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
reader.settimeout(query_interval)

def handle_responses(peers: set, handle_peer_found):
  while True:
    try:
      data, (peer_ip, peer_port) = reader.recvfrom(buffer_size)
    except socket.timeout:
      return

    if data == query_msg:
      continue
    hostname = data.decode('utf-8')
    key = (hostname, peer_ip)
    if key in peers:
      continue
    peers.add(key)

    handle_peer_found(*key)

def search_for_peers(num_probes: int, handle_peer_found):
  peers = set()
  for _ in range(num_probes):
    writer.sendto(query_msg, (multicast_group, multicast_port))
    handle_responses(peers, handle_peer_found)

def main():
  def handle_peer_found(hostname, peer_ip):
    print('peer:', hostname, peer_ip)
  search_for_peers(5, handle_peer_found)

try:
  main()
except KeyboardInterrupt:
  pass
