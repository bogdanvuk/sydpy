#  This file is part of sydpy.
# 
#  Copyright (C) 2014-2015 Bogdan Vukobratovic
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

from sydpy.component import RequiredFeature, Component, compinit

class EventSet(Component):
    """Container for events."""
    @compinit
    def __init__(self, events = {}, missing_event_handle=None, dynamic=True, **kwargs):
        self.events = events.copy()
        
        if missing_event_handle:
            self.missing_event = missing_event_handle
        elif dynamic:
            self.missing_event = self._missing_event
        else:
            self.missing_event = self._missing_event_err

    def _missing_event(self, _, name):
        return self.inst(name, Event)

    def _missing_event_err(self, _, name):
        raise Exception("no such event")
    
    def __getattr__(self, name):
        try:
            return Component.__getattr__(self, name)
        except AttributeError:
            return self.missing_event(self, name)

class Event(Component):
    sim = RequiredFeature('sim')

    """Class that allows processes to register to it. When the Event is 
    triggered, it activates all processes that registered to it."""
    @compinit
    def __init__(self, parent=None, key=None, **kwargs):
        """Create a new Event.
        
        parent  - The object that created the event
        name    - The name of the event
        key     - If the event should be triggered on changes of the part 
                  of the data, key is the index of that data part.
        """
        self.parent = parent
        self.pool = set()
        self.key = key
        self.subevents = {}
        
    def unsubscribe(self, obj):
        self.pool.remove(obj)

    def subscribe(self, obj):
        self.pool.add(obj)
        
    def trigger(self):
        self.sim.trigger(self)
    
    def resolve(self, pool):
#         print(str(self))
        
        for s in self.pool:
            if hasattr(s, 'resolve'):
                s.resolve(pool)
            else:
                pool.add(s)    
        