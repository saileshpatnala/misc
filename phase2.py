from math import log
from math import pow
from math import exp
from random import random
import queue

# global variables
num_hosts = 10 # number of hosts
num_packets = 100000 # number of packets
MAX_BUFFER = float("inf") # maximum queue size
mu = 1 # arrival rate
lamda = 0.1 # service rate 

# for keeping track of stats
global_time = 0.0 # current time
previous_time = 0.0 # previous event time
tota_bytes = 0 # number of bytes successfully transmitted
total_delay = 0 # total delay for all hosts
channel_busy = False # transmission channel in use 

#
# Event Class
#
class Event:
  def __init__(self, event_time = -1, event_type = 'N', sub_type = -1, src = 0, dest = 0, size = 0, _next = None, _prev = None):
    self.event_time = event_time
    self.event_type = event_type # A for arrival, D for departure, C for channel-sensing, T for timeout event
    self.event_sub_type = sub_type # 0 for handshake, 1, data packet, 2 for ack
    self.source = src
    self.destination = dest
    self.size = size
    self._next = _next # for double linked_list implementation
    self._prev = _prev # for double linked list implementation

#
# Packet Class
#
class Packet:
  def __init__(self, service_time = 0.0, size = 0.0):
    self.service_time = service_time
    self.size = size

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
  def __init__(self, length, packets_dropped = 0, backoff_n = 0, backoff_counter = 0, transmission_time = 0.0, queueing_time = 0.0):
    self.buffer = queue.Queue()
    self.buffer_length = length
    self.packets_dropped = packets_dropped
    self.backoff_n = backoff_n
    self.backoff_counter = backoff_counter
    self.transmission_time = transmission_time
    self.queueing_time = queueing_time

# generate random time from negative exponential distribuiton
def neg_exp_dist_time(rate):
  u = random()
  return ((-1 / rate) * log(1- u))

# process handshake arrival event
def process_handshake_arrival_event(gel, channel):
  return

# process data packet arrival event
def process_data_packet_arrival_event(gel, channel):
  return

# process ack packet arrival event
def process_ack_packet_arrival_event(gel, channel):
  return

# process data packet departure event
def process_data_packet_departure_event(gel, channel):
  return

# process ack packet departure event
def process_ack_packet_departure_event(gel, channel):
  return

def main():
  global num_hosts
  global num_packets
  global MAX_BUFFER
  global mu
  global lamda
  global global_time
  global previous_time
  global total_bytes
  global total_delay
  global channel_busy

  # initialization
  gel = EventList()
  channel = EventList()

  hosts = [Host() for i in range(0, num_hosts)]
  for i in range(0, num_hosts):
    temp = Event() # handshake arrival event
    temp.event_time = 0
    temp.event_type = 'A'
    temp.event_sub_type = 0 
    temp.source = i
    gel.insert(temp)

  Event head = gel.get_head()
  previous_time = head.event_time

  # iteration
  for i in range(0, num_packets):
    curr_event = gel.get_head()
    global_time = curr_event.event_time

    # process arrival events
    if curr_event.event_type == 'A':
      # process handshake arrival event
      if curr_event.event_sub_type == 0:
        process_handshake_arrival_event(gel, channel)

      # process data packet arrival event
      elif curr_event.event_sub_type == 1:
        process_data_packet_arrival_event(gel, channel)

      # process ack packet arrival event
      elif curr_event.event_sub_type == 2:
        process_ack_packet_arrival_event(gel, channel)

    # process departure events
    elif curr_event.event_type == 'D':
      # process data packet departure event
      if curr_event.event_sub_type == 1:
        process_data_packet_departure_event(gel, channel)

      # process ack packet departure event
      elif curr_event.event_sub_type == 2:
        process_ack_packet_departure_event(gel, channel)

  return

if __name__ == '__main__':
  main()
