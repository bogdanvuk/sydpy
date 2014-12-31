#  This file is part of sydpy.
# 
#  Copyright (C) 2014 Bogdan Vukobratovic
#
#  sydpy is free software: you can redistribute it and/or modify 
#  it under the terms of the GNU Lesser General Public License as 
#  published by the Free Software Foundation, either version 2.1 
#  of the License, or (at your option) any later version.
# 
#  sydpy is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
# 
#  You should have received a copy of the GNU Lesser General 
#  Public License along with sydpy.  If not, see 
#  <http://www.gnu.org/licenses/>.

"""Module implements Event and EventSet classes"""

from sydpy._simulator import simtrig 
from sydpy._util._util import key_repr

class EventSet(object):
    """Container for events."""
    def __init__(self, events = {}, missing_event_handle=None):
        self.events = events.copy()
        
        if missing_event_handle:
            self.missing_event = missing_event_handle
        else:
            self.missing_event = self._missing_event

    def _missing_event(self, e):
        raise Exception("no such event")
    
    def __getattr__(self, e):
        if e in self.events:
            return self.events[e]
        else:
            return self.missing_event(self, e)
    
    def __contains__(self, e):
        return e in self.events
      
    def add(self, *args, **kwargs):
        self.events.update(*args, **kwargs)
        
    def __iter__(self):
        return iter(self.events)
    
    def __getitem__(self, key):
        return self.events[key]

class Event(object):
    """Class that allows processes to register to it. When the Event is 
    triggered, it activates all processes that registered to it."""
    def __init__(self, parent=None, name="", key=None):
        """Create a new Event.
        
        parent  - The object that created the event
        name    - The name of the event
        key     - If the event should be triggered on changes of the part 
                  of the data, key is the index of that data part.
        """
        self.parent = parent
        self.pool = set()
        self.name = name
        self.key = key
        self.subevents = {}
        
    def unsubscribe(self, obj):
        self.pool.remove(obj)

    def subscribe(self, obj):
        self.pool.add(obj)
        
    def trigger(self):
        simtrig(self)
        
    def resolve(self, pool):
        print(str(self))
        
        for s in self.pool:
            try:
                s.resolve(pool)
            except AttributeError:
                pool.append(s)
    
    def _hdl_gen_ref(self, conv):
        return self.name + ' ' + conv._hdl_gen_ref(self.parent)
    
    def __getitem__(self, key):
        if repr(key) not in self.subevents:
            name = self.name + key_repr(key)
            subevent = Event(self.parent, name, key=key)
            self.subevents[repr(key)] = subevent
        else:
            subevent = self.subevents[repr(key)]
        return subevent
    
    def __str__(self):
        return  self.parent.qualified_name + "." + self.name 
        
    def __repr__(self):
        return  self.parent.qualified_name + "." + self.name

    
        