import socket
import time
import struct
import threading

def multi_listener(running_cb, multicast_group: str, multicast_port: int, length: int):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
  sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEPORT, 1)
  sock.bind((multicast_group, multicast_port))
  mreq = struct.pack("4sl", socket.inet_aton(multicast_group), socket.INADDR_ANY)

  sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
  sock.settimeout(1)

  # a quick google search says 508 bytes is the smallest fragmentation size of
  # something. that's good enough for broadcasting ip addresses.
  while running_cb():
    try:
      data = sock.recv(length)
    except socket.timeout:
      continue
    print('data:', data.decode('utf-8'))

def multi_sender(running_cb, multicast_group: str, multicast_port: int, multicast_ttl: int, msg: bytes, sleep: int):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_IP)
  sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, multicast_ttl)
  while running_cb():
    sock.sendto(msg, (multicast_group, multicast_port))
    time.sleep(sleep)

def main():
  multicast_group = '224.1.1.1'
  multicast_port = 5007
  multicast_ttl = 1
  msg = b'robot'
  running = True
  sleep = 1

  def running_cb():
    return running

  send_thread = threading.Thread(target=multi_sender, args=(running_cb, multicast_group, multicast_port, multicast_ttl, msg, sleep))
  listen_thread = threading.Thread(target=multi_listener, args=(running_cb, multicast_group, multicast_port, len(msg)))

  try:
    send_thread.start()
    listen_thread.start()
    send_thread.join()
    listen_thread.join()
  except KeyboardInterrupt:
    running = False
  finally:
    send_thread.join()
    listen_thread.join()

if __name__ == '__main__':
  main()