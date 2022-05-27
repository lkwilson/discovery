#!/usr/bin/env python

import socket
import struct
import sys
import threading
import time
from typing import Callable, Optional


def setup_multicast_sender(multicast_ttl: int = 1):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
  sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, multicast_ttl)
  return sock

def setup_multicast_listener(multicast_group: str = '224.1.1.1', multicast_port: int = 5007, timeout: Optional[float] = 5):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
  sock.bind((multicast_group, multicast_port))
  mreq = struct.pack("4sl", socket.inet_aton(multicast_group), socket.INADDR_ANY)
  sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
  if timeout is not None:
    sock.settimeout(timeout)
  return sock

def read(sock: socket.socket, is_running: Callable = None, buffer_size: int = 508):
  if is_running is None:
    def is_running():
      return True
  while is_running():
    try:
      return sock.recvfrom(buffer_size)
    except socket.timeout:
      continue

def write(sock: socket.socket, data: bytes, multicast_group: str = '224.1.1.1', multicast_port: int = 5007):
  sock.sendto(data, (multicast_group, multicast_port))


def main():
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
    listener = setup_multicast_listener()
    sender = setup_multicast_sender()
    friends = set()
    enemy = set()
    while is_running():
      data, (peer_ip, peer_port) = read(listener, is_running=is_running)
      if data == error_msg:
        pass
      elif data == response_msg:
        if peer_ip in friends:
          continue
        print('Found peer:', peer_ip)
        friends.add(peer_ip)
      elif data == query_msg:
        write(sender, response_msg)
      elif peer_ip not in enemy:
        print("Found enemy!", peer_ip)
        enemy.add(peer_ip)
        write(sender, error_msg)

  def start_cartographer():
    sender = setup_multicast_sender()
    while is_running():
      write(sender, query_msg)
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
