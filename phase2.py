#
# Event Class
#
class Event:
  def __init__(self, event_time = 1, event_type = 'N', _next = None, _prev = None):
    self.event_time = event_time
    self.event_type = event_type
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
      

