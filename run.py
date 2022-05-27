#!/usr/bin/env python

import socket
import struct
import sys
import threading
import time
from typing import Optional


def setup_multicast_sender(multicast_ttl: int):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
  sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, multicast_ttl)
  return sock

def setup_multicast_listener(multicast_group: str, multicast_port: int, timeout: Optional[float]):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
  sock.bind((multicast_group, multicast_port))
  mreq = struct.pack("4sl", socket.inet_aton(multicast_group), socket.INADDR_ANY)
  sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
  if timeout is not None:
    sock.settimeout(timeout)
  return sock


def main():
  multicast_group = '224.1.1.1'
  multicast_port = 5007
  multicast_ttl = 1
  wait_interval = 5
  query_interval = 0.5
  buffer_size = 508  # avoid fragmentation
  # buffer_size = 65_507  # don't care about fragmentation
  # buffer_size = 10240  # good enough

  query_msg = b'Hey, whose all out there?'
  response_msg = b"I'm here! What's up?"
  error_msg = b'Hey, get out of our multicast group!'

  running = True
  threads: list[threading.Thread] = []

  def is_running():
    return running

  def start_lighthouse():
    listener = setup_multicast_listener(multicast_group, multicast_port, wait_interval)
    sender = setup_multicast_sender(multicast_ttl)
    friends = set()
    enemy = set()
    while is_running():
      try:
        data, (peer_ip, peer_port) = listener.recvfrom(buffer_size)
      except socket.timeout:
        # allow reraise of interrupt
        continue
      if data == error_msg:
        pass
      elif data == response_msg:
        if peer_ip in friends:
          continue
        print('Found peer:', peer_ip)
        friends.add(peer_ip)
      elif data == query_msg:
        sender.sendto(response_msg, (multicast_group, multicast_port))
      elif peer_ip not in enemy:
        print("Found enemy!", peer_ip)
        enemy.add(peer_ip)
        sender.sendto(error_msg, (multicast_group, multicast_port))

  def start_cartographer():
    sender = setup_multicast_sender(multicast_ttl)
    while is_running():
      sender.sendto(query_msg, (multicast_group, multicast_port))
      time.sleep(query_interval)

  if len(sys.argv) < 2:
    print(sys.argv[0], '<search|watch>...')
    return
  funcs = set()
  for mode in sys.argv[1:]:
    if mode == 'search':
      funcs.add(start_cartographer)
    elif mode == 'watch':
      funcs.add(start_lighthouse)
    else:
      print(sys.argv[0], '<search|watch>...')
      return

  try:
    for func in funcs:
      thread = threading.Thread(target=func)
      thread.start()
      threads.append(thread)
    for thread in threads:
      thread.join()
  except BaseException:
    running = False
  finally:
    for thread in threads:
      if thread.is_alive():
        thread.join()

if __name__ == '__main__':
  main()
