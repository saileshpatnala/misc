from math import log, pow, exp
from random import random, uniform, expovariate


# global variables
num_hosts = 10 # number of hosts
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
previous_time = 0.0 # previous event time
tota_bytes = 0 # number of bytes successfully transmitted
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
  def __init__(self, event_time = -1, event_type = 'N', event_sub_type = -1, src = 0, dest = 0, size = 0, corrupt = False, _next = None, _prev = None):
    self.time = event_time
    self.type = event_type
    # A for arrival, D for departure, C for channel-sensing, T for timeout 
    self.sub_type = event_sub_type 
    # for arrival events: 0 for genesis, 1 for data packet, 2 for ack packet
    # for departure events: 0 for genesis, 1 for ack packet
    self.source = src
    self.destination = dest
    self.size = size
    self.is_corrupt = corrupt
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
  def __init__(self, length = 0, packets_dropped = 0, backoff_n = 0, backoff_counter = 0, transmission_time = 0.0, queueing_time = 0.0):
    self.buffer = Buffer() 
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

# set initial backoff conuter values for hosts
# all hosts must have different values
def initialize_backoff_counter(hosts):
  global num_hosts

  selected_backoff_value = []
  i = 0
  while i < num_hosts:
    u = uniform(0, t_value)
    if u not in selected_backoff_value:
      selected_backoff_value.append(u)
      hosts[i].backoff_counter = u
      i += 1
  return

# reset backoff counter for host when there is a timeout
# all hosts much have different values
def reset_backoff_counter(hosts):
  return

def generate_packet_size():
  u = expovariate(0.001)
  while u > 1544:
    u = expovariate(0.001)

  return u


# process arrival event
def process_arrival_event(curr_event, hosts, gel, channel):
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
  next_arrival_event = Event()
  next_arrival_event.type = 'A'
  next_arrival_event.sub_type = 0
  next_arrival_event.source = curr_event.source
  next_arrival_event.time = global_time + neg_exp_dist_time(lamda)
  
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
    departure_event = Event()
    departure_event.type = 'D'
    departure_event.sub_type = 0
    departure_event.source = curr_event.source
    departure_event.time = global_time + new_packet.service_time
    departure_event.destination = curr_event.destination

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

# process data packet arrival event
def process_data_packet_arrival_event(curr_event, hosts, gel, channel):
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

  # currently transmitting host
  curr_host = hosts[curr_event.source]

  e = channel.get_head()
  if e.is_corrupt == False:
    # create ack departure event
    ack_departure_event = Event()
    ack_departure_event.type = 'D'
    ack_departure_event.source = curr_event.source
    ack_departure_event.sub_type = 1
    ack_departure_event.destination = curr_event.destination
    ack_departure_event.size = curr_event.size
    ack_departure_event.time = global_time + SIFS

    # insert ack departure event into gel
    gel.insert(ack_departure_event)

  #elif e.is_corrupt == True:
    # do nothing

  else:
    print('ERROR: data packet arrival error')

  curr_host.transmission_time += (curr_event.size/(11000000/8))
  channel.remove_head()

  return

# process ack packet arrival event
def process_ack_packet_arrival_event(curr_event, hosts, gel, channel):
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

  # currently transmitting host
  curr_host = hosts[curr_event.source]
  
  if channel.size == 1:
    total_bytes += 64
    total_bytes += curr_event.size

    # pop packet once done processing
    curr_host.buffer.pop()
    curr_host.buffer_length -= 1

    # create next departure event
    next_departure_event = Event()
    next_departure_event.type = 'D'
    next_departure_event.source = curr_event.source
    next_departure_event.sub_type = 0
    new_packet = curr_host.buffer.front()
    next_departure_event.time = global_time + new_packet.service_time
    next_departure_event.destination = curr_event.destination

    # insert departure event into gel
    gel.insert(next_departure_event)

    # set backoff_n
    #curr_host.backoff_n = 1

  #elif channel.size > 1:
    # do nothing 

  else:
    print('ERROR: ack packet arrival error')

  curr_host.transmission_time += (64/(11000000/8))
  channel.remove_head()

  return

# process data packet departure event
def process_departure_event(curr_event, hosts, gel, channel):
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

  #currently transmitting host
  curr_host = hosts[curr_event.source]

  new_packet = curr_host.buffer.front()
  curr_host.queueing_time += new_packet.service_time

  if curr_host.buffer_length > 0:
    # if channel is free
    if channel.size == 0:
      # create arrival event for new host
      new_arrival_event = Event()
      new_arrival_event.type = 'A'
      new_arrival_event.source = curr_event.destination
      new_arrival_event.destination = curr_event.source
      new_arrival_eventtime = global_time + (new_packet.size / (11000000/8)) + DIFS
      new_arrival_event.size = new_packet.size
      new_arrival_event.sub_type = 1

      # insert new arrival event into gel
      gel.insert(new_arrival_event)

      # create timeout event
      new_timeout_event = Event()
      new_timeout_event.type = 'T'
      new_timeout_event.source = curr_event.source
      new_timeout_event.destination = curr_event.destination
      new_timeout_event.time = global_time + SIFS + (new_packet.size / (11000000/8)) + (64 / (11000000/8)) + delta_t

      # insert timeout event into gel
      gel.insert(new_timeout_event)

    # if channel is not free
    elif channel.size > 0:
      # FIXME: choose random backoff value
      # reset backoff values for each host

      # create channel sensing event
      new_channel_sensing_event = Event()
      new_channel_sensing_event.type = 'C'
      new_channel_sensing_event.source = curr_event.source
      new_channel_sensing_event.time = global_time + 0.01
      new_channel_sensing_event.destination = curr_event.destination

      # insert channel sensing event into gel
      gel.insert(new_channel_sensing_event)

    else:
      print('ERROR: data packet departure error')
  return

# process ack packet departure event
def process_ack_packet_departure_event(curr_event, hosts, gel, channel):
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

  # currently transmitting host
  curr_host = hosts[curr_event.source]

  if channel.size == 0:
    # create new ack packet arrival event
    new_ack_packet_arrival_event = Event()
    new_ack_packet_arrival_event.type = 'A'
    new_ack_packet_arrival_event.sub_type = 2
    new_ack_packet_arrival_event.source = curr_event.destination
    new_ack_packet_arrival_event.size = curr_event.size
    new_ack_packet_arrival_event.destination = new_arrival_event.source
    new_ack_packet_arrival_event.time = global_time + (64 / (11000000/8))

    # insert new arrival event into gel 
    gel.insert(new_arrival_event)

  #elif channel.size > 0:
    # FIXME: make all events in channel corrupt

  return

# process channel sensing event
def process_channel_sensing_event(curr_event, hosts, gel, channel):
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

  curr_host = hosts[curr_event.source]
  # if channel is free
  if channel.size == 0:
    curr_host.backoff_counter -= 1
    if curr_host.backoff_counter == 0:
      new_packet = curr_host.buffer.front()
      global_time = curr_event.time

      # create data packet arrival event
      new_arrival_event = Event()
      new_arrival_event.type = 'A'
      new_arrival_event.source = curr_event.destination
      next_arrival_event.time = global_time + (new_packet.size / (11000000/8)) + DIFS
      new_arrival_event.size = new_packet.size
      new_arrival_event.sub_type = 1

      # insert new data packet arrival event into gel
      gel.insert(new_arrival_event)

    else:
      print('ERROR: data corruption check')

    new_timeout_event = Event()
    new_timeout_event.type = 'T'
    new_timeout_event.source = curr_event.source
    new_timeout_event.time = global_time + SIFS + (new_packet.size / (11000000/8)) + (64 / (11000000/8)) + delta_t

    # insert new timeout event into gel
    gel.insert(new_timeout_event)

  elif channel.size > 0:
    # create new channel sensing event
    new_channel_sensing_event = Event()
    new_channel_sensing_event.source = curr_event.source
    new_channel_sensing_event.time = time + 0.01
    new_channel_sensing_event.destination = curr_event.destination

    # insert new channel sensing event into gel
    gel.insert(new_channel_sensing_event)

  else:
    print('ERROR: channel sensing error')

  return

# process timeout event
def process_timeout_event(curr_event, hosts, gel, channel):
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

  curr_host = hosts[curr_event.source]

  curr_hosts.backoff_n += 1
  new_packet = curr_host.buffer.front()

  # create departure event
  new_departure_event = Event()
  new_departure_event.type = 'D'
  new_departure_event.source = curr_event.source
  new_departure_event.time = global_time + new_packet.service_time
  new_departure_event.destination = curr_event.destination
  new_departure_event.sub_type = 0

  # insert departure event into gel
  gel.insert(new_departure_event)

  return

def output_statistics(hosts):
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

  for i in range(0, num_hosts):
    total_delay += hosts[i].transmission_time + hosts[i].queueing_time

  throughput = total_bytes / global_time
  avg_network_delay = total_delay / throughput

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
  channel = EventList()

  hosts = [Host() for i in range(0, num_hosts)]
  for i in range(0, num_hosts):
    e = Event()
    e.type = 'A'
    e.source = i
    e.time = global_time + neg_exp_dist_time(lamda)
    e.sub_type = 0 
    gel.insert(e)

  head = gel.get_head()
  previous_time = head.time

  # iteration
  for i in range(0, num_packets):
    curr_event = gel.get_head()
    global_time = curr_event.time

    # process arrival events
    if curr_event.type == 'A':
      # process genesis arrival event
      if curr_event.sub_type == 0:
        process_arrival_event(curr_event, hosts, gel, channel)

      # process data packet arrival event
      elif curr_event.sub_type == 1:
        process_data_packet_arrival_event(curr_event, hosts, gel, channel)

      # process ack packet arrival event
      elif curr_event.sub_type == 2:
        process_ack_packet_arrival_event(curr_event, hosts, gel, channel)

    # process departure events
    elif curr_event.type == 'D':
      # process data packet departure event
      if curr_event.sub_type == 0:
        process_departure_event(curr_event, hosts, gel, channel)

      # process ack packet departure event
      elif curr_event.sub_type == 1:
        process_ack_packet_departure_event(curr_event, hosts, gel, channel)

    # process channel-sensing event
    elif curr_event.type == 'C':
      process_channel_sensing_event(curr_event, hosts, gel, channel)

    #process timeout event
    elif curr_event.type == 'T':
      process_timeout_event(curr_event, hosts, gel, channel)

    else:
      # throw error
      print('ERROR: type NOT RECOGNIZED')

    gel.remove_head()
    previous_time = global_time

  output_statistics(hosts)

  return

if __name__ == '__main__':
  main()
