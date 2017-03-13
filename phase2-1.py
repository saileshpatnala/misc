"""""""""""""""""""""""""""""""""
#                               #
# Sailesh Patnala (912044277)   #
# Rishab Sanyal (_________)     #
# ECS 152A Phase 2 Simulation   #
#                               #
"""""""""""""""""""""""""""""""""

# FIXME: thinking about getting rid of timeout events

from math import log, pow, exp
from random import random, uniform, expovariate, randint

# global variables
num_hosts = 5 # number of hosts
num_packets = 100000 # number of packets
MAX_BUFFER = float("inf") # maximum queue size
mu = 1 # service rate
lamda = 0.1 # arrival rate 
DIFS = 0.1 # distributed inter-frame space time (msec)
SIFS = 0.05 # short inter-frame space time (msec)
channel_busy = False # transmission channel in use 
t_value = 10 # for backoff_n
delta_t = 15 # timeout value (msec)

# for keeping track of stats
global_time = 0.0 # current time
total_bytes = 0 # number of bytes successfully transmitted
total_delay = 0 # total delay for all hosts

#
# Queue Class
#
class Buffer:
  def __init__(self):
    self.data = []

  def push(self, item):
    self.data.insert(0, item)

  def pop(self):
    return self.data.pop()

  def size(self):
    return len(self.data)

  def front(self):
    return self.data[0]

#
# Event Class
#
class Event:
  def __init__(self, event_time = -1, event_type = 'N', src = 0, dest = 0, size = 0, corrupt = False, _next = None, _prev = None):
    self.time = event_time
    self.type = event_type
    # A for arrival, D for departure, K for ack, C for channel-sensing, T for timeout 
    self.source = src
    self.destination = dest
    self.size = size
    self.is_corrupt = corrupt
    self._next = _next # for double linked_list implementation
    self._prev = _prev # for double linked list implementation

def new_event(_type, src, time):
  e = Event()
  e.type = _type
  e.source = src
  # set random destination
  e.destination = randint(0, num_hosts-1)
  # make sure destination != source
  while e.source == e.destination:
    e.destination = randint(0, num_hosts-1)

  if _type == 'A':
    e.time = time + neg_exp_dist_time(lamda)

  elif _type == 'D':
    e.time = time + neg_exp_dist_time(mu)

  elif _type == 'S':
    e.time = time + 0.01

  else:
    e.time = time

  return e

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
    self.size = 0

  # in order insert for linked list
  def insert(self, event):
    self.size += 1
    if self.head is None:
      self.head = event
    elif self.head.time > event.time:
      event._next = self.head
      self.head._prev = event
      self.head = event
    else:
      prev = self.head
      cur = self.head._next
      while cur is not None:
        if cur.time > event.time:
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
    self.size -= 1
    if self.head == None:
      print('ERROR: linked list remove_head out of bounds')
      return
    head_next = self.head._next
    if head_next == None:
      self.head = None
    if head_next is not None:
      head_next._prev = None
      self.head = head_next

  def at(self, index):
    cur = self.head
    for i in range(0, index):
      cur = cur._next

    return cur
    
  # print elements in linked list
  def show(self):
    curr = self.head
    while curr != self.tail:
      print(curr.time)
      curr = curr._next

#
# Host Class
#
class Host:
  def __init__(self, length = 0, packets_dropped = 0, backoff_n = 1, backoff_counter = 0, transmission_time = 0.0, queueing_time = 0.0, timeout = 0.0):
    self.buffer = Buffer() 
    self.buffer_length = length 
    self.packets_dropped = packets_dropped 
    self.backoff_n = backoff_n 
    self.backoff_counter = backoff_counter 
    self.transmission_time = transmission_time 
    self.queueing_time = queueing_time 
    self.timeout = timeout

# generate random time from negative exponential distribuiton
def neg_exp_dist_time(rate):
  u = random()
  return ((-1 / rate) * log(1- u))

# generate random negative exponentially distributed packet size
def generate_packet_size():
  u = expovariate(0.001)
  while u > 1544:
    u = expovariate(0.001)
  return u

# set initial backoff conuter values for hosts
# all hosts must have different values
def initialize_backoff_counter(hosts):
  global num_hosts
  selected_backoff_values = []
  i = 0
  while i < num_hosts:
    u = round(uniform(0, t_value))
    if u not in selected_backoff_values:
      selected_backoff_values.append(u)
      hosts[i].backoff_counter = u
      i += 1
  return

# reset backoff counter for hosts
# all hosts must have different values
def reset_backoff_counter(curr_host, hosts):
  global num_hosts
  selected_backoff_values = [hosts[i].backoff_counter for i in range(0, num_hosts)]
  u = round(uniform(0, hosts[i].backoff_n * t_value))
  while u in selected_backoff_values:
    u = round(uniform(0, hosts[i].backoff_n * t_value))

  curr_host.backoff_counter = u
  return

def process_arrival_event(curr_event, hosts, gel):
  global num_hosts
  global num_packets
  global MAX_BUFFER
  global mu
  global lamda
  global DIFS
  global SIFS
  global channel_busy
  global t_value
  global delta_t
  global global_time
  global previous_time
  global total_bytes
  global total_delay

  # create next arrival event
  next_arrival_event = new_event('A', curr_event.source, global_time)
  next_arrival_event.sub_type = 0
  
  # insert next arrival event into gel
  gel.insert(next_arrival_event)

  new_packet = Packet()
  new_packet.size = generate_packet_size()
  new_packet.service_time = neg_exp_dist_time(mu)

  # currently transmitting host
  curr_host = hosts[curr_event.source]

  # buffer is empty
  if curr_host.buffer_length == 0:
    # push packet onto queue
    curr_host.buffer.push(new_packet)
    curr_host.buffer_length += 1

    # create departure event
    departure_event = new_event('D', curr_event.source, global_time)
    departure_event.destination = curr_event.destination
    departure_event.time = global_time + new_packet.service_time

    # insert departure event into gel
    gel.insert(departure_event)

  # buffer is neither full nor empty
  elif curr_host.buffer_length > 0 and curr_host.buffer_length < MAX_BUFFER:
    curr_host.buffer.push(new_packet)
    curr_host.buffer_length += 1

  # buffer is full
  else:
    curr_host.packets_dropped += 1

  return

def process_departure_event(curr_event, hosts, gel):
  # currently transmitting host
  curr_host = hosts[curr_event.source]

  packet = curr_host.buffer.front()
  curr_host.queueing_time += packet.service_time

  if channel_busy == False:
    # create ack event
    ack_event = new_event('K', curr_event.destination, global_time)
    ack_event.destination = curr_event.source
    ack_event.time = global_time + ((packet.size * 8)/ 11000000) + DIFS # FIXME: confirm this time

    #insert ack event into gel
    gel.insert(ack_event)

    # set timeout value for curr_host
    curr_host.timeout = global_time + 15

  elif channel_busy == True:
    # reset backoff_counter
    reset_backoff_counter(curr_host, hosts)

    # create sensing event
    sensing_event = new_event('S', curr_event.source, global_time)
    sensing_event.destination = curr_event.destination
    sensing_event.time = global_time + 0.01

    # insert sensing event into gel
    gel.insert(sensing_event)

  return

def process_ack_event(curr_event, hosts, gel):
  # currently transmitting host
  curr_host = hosts[curr_event.source]

  # destination host for ack
  dest_host = hosts[curr_event.destination]

  # if channel is free
  if channel_busy == False:
    # if ack didn't timeout
    if dest_host.timeout < curr_event.time:
      # packet has been transmitted
      packet = dest_host.buffer.pop()
      dest_host.buffer_length -= 1

      # increase total bytes processed
      total_bytes += 64
      total_bytes += packet.size

      dest_host.backoff_n = 1

    # if ack timeout
    else:
      packet = dest_host.buffer.front()
      # increment backoff n value
      dest_host.backoff_n += 1
      # retransmit the packet - create new departure event
      new_departure_event = new_event('D', curr_event.destination, global_time)
      new_departure_event.destination = curr_event.source
      new_departure_event.time = global_time + packet.service_time

    if channel_busy == True:
      # reset backoff_counter
      reset_backoff_counter(curr_host, hosts)

      # create new_ack_event
      new_ack_event = new_event('K', curr_event.source, global_time)
      new_ack_event.destination = curr_event.destination
      ack_event.time = global_time + ((packet.size * 8)/ 11000000) + DIFS # FIXME: confirm this time

  return

def process_sensing_event(curr_event, hosts, gel):
  # create next sensing event
  next_sensing_event = new_event('S', curr_event.source, global_time)
  next_sensing_event.destination = curr_event.destination
  next_sensing_event.time = global_time + 0.01

  # if channel is free
  if channel_busy == False:
    # decrement backoff counter for current host
    curr_host.backoff_counter -= 1

  # else:
    # do nothing

  return

# def process_timeout_event(curr_event, hosts, gel):
#   return

def output_statistics(hosts):
  global num_hosts
  global global_time
  global total_bytes
  global total_delay

  for i in range(0, num_hosts):
    total_delay += hosts[i].transmission_time + hosts[i].queueing_time

  throughput = (total_bytes / global_time)
  if throughput == 0:
    avg_network_delay = 0
  else:
    avg_network_delay = (total_delay / throughput)

  print('Throughput: ', throughput)
  print('Average Network Delay: ', avg_network_delay)

  return


def main():
  global num_hosts
  global num_packets
  global MAX_BUFFER
  global mu
  global lamda
  global DIFS
  global SIFS
  global channel_busy
  global t_value
  global delta_t
  global global_time
  global previous_time
  global total_bytes
  global total_delay

  # initialization
  gel = EventList()
  hosts = [Host() for i in range(0, num_hosts)]
  for i in range(0, num_hosts):
    e = new_event('A', i, global_time)
    gel.insert(e)
  initialize_backoff_counter(hosts)

  head = gel.get_head()

  # simulation
  for i in range(0, num_packets):
    curr_event = gel.get_head()
    global_time = curr_event.time

    # process arrival events
    if curr_event.type == 'A':
      process_arrival_event(curr_event, hosts, gel)

    # process departure events
    elif curr_event.type == 'D':
      process_departure_event(curr_event, hosts, gel)

    # process ack events
    elif curr_event.type == 'K':
      process_ack_event(curr_event, hosts, gel)

    # process sensing events
    elif curr_event.type == 'C':
      process_sensing_event(curr_event, hosts, gel)

    # process timeout events
    # elif curr_event.type == 'T':
    #   process_timeout_event(curr_event, hosts, gel)

    else:
      # throw error
      print('ERROR: event.type NOT RECOGNIZED')

    gel.remove_head()

  output_statistics(hosts)

  return 

if __name__ == '__main__':
  main()