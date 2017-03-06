from math import log
from math import pow
from math import exp
from random import random
import queue

# global variables
num_hosts = 0 # number of hosts
MAX_BUFFER = float("inf")
mu = 1 # arrival rate
lamda = 0.1 # service rate 

# for keeping track of stats
global_time = 0.0
tota_bytes = 0
total_delay = 0

#
# Event Class
#
class Event:
  def __init__(self, event_time = 1, event_type = 'N', _next = None, _prev = None):
    self.event_time = event_time
    self.event_type = event_type # A for arrival, D for departure, C for channel-sensing, T for timeout event
    self._next = _next
    self._prev = _prev

  def get_event_type(self):
    return event_type

  def set_event_type(self, _type):
    self.event_type = _type

  def get_event_time(self):
    return event_time

  def set_event_time(self, time):
    self.event_time = time


#
# Packet Class
#
class Packet:
  def __init__(self, service_time = 0.0):
    self.service_time = service_time

  def get_service_time(self):
    return self.service_time

#
# EventList Class
#
class EventList:
  def __init__(self):
    self.head = None
    self.tail = None

  # in order insert for linked list
  def insert(self, event):
    if self.head is None:
      self.head = event
    elif self.head.get_event_time() > event.get_event_time():
      event._next = self.head
      self.head._prev = event
      self.head = event
    else:
      prev = self.head
      cur = self.head._next
      while cur is not None:
        if cur.get_event_time() > event.get_event_time():
          prev._next = event
          event._prev = prev
          event._next = cur
          cur._prev = event
          return
        prev = cur
        cur = cur._next
      prev._next = event
      event._prev = prev

  # get head from linked list
  def get_head(self):
    return self.head

  # remove head from linked list
  def remove_head(self):
    head_next = self.head._next
    head_next._prev = None
    self.head = head_next
    
  # print elements in linked list
  def show(self):
    curr = self.head
    while curr != self.tail:
      print(curr.get_event_time())
      curr = curr._next

#
# Host Class
#
class Host:
  def __init__(self, length, packets_dropped, backoff_n, backoff_counter, transmission_time, queueing_time):
    self.buffer = queue.Queue()
    self.buffer_length = length
    self.packets_dropped = packets_dropped
    self.backoff_n = backoff_n
    self.backoff_counter = backoff_counter
    self.transmission_time = transmission_time
    self.queueing_time = queueing_time

  def get_buffer_length(self):
    return self.buffer_length

  def set_buffer_length(self, length):
    self.buffer_length = length

  def get_packets_dropped(self):
    return packets_dropped

  def set_packets_dropped(self, dropped):
    self.packets_dropped = dropped

  def get_backoff_n(self):
    return backoff_n

  def set_backoff_n(self, n):
    self.backoff_n = n

  def get_backoff_counter(self):
    return backoff_counter

  def set_backoff_counter(self, count):
    self.backoff_counter = count

  def get_transmission_time(self):
    return self.transmission_time

  def set_transmission_time(self, time):
    self.transmission_time = time

  def get_queueing_time(self):
    return self.queueing_time

  def set_queueing_time(self, time):
    self.queueing_time = time

# generate random timr from negative exponential distribuiton
def neg_exp_dist_time(rate):
  u = random()
  return ((-1 / rate) * log(1- u))

def main():
  global num_hosts
  global MAX_BUFFER
  global mu
  global lamda
  global global_time
  global total_bytes
  global total_delay

  return

if __name__ == '__main__':
  main()
