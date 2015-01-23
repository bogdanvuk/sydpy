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

"""Module implements Signal class"""

from sydpy._delay import Delay 
from sydpy._component import Component
from sydpy._simulator import simupdate, simwait
from enum import Enum

class SignalMem(Enum):
    signal = 0
    queue = 1
    stack = 2
    delta_queue = 3
    
class SignalType(Enum):
    signal = 0
    queue = 1
    stack = 2
    delta_queue = 3

class SignalQueueEmpty(Exception):
    pass

class Signal(object):
    """Signal is smallest unit that provides evaluate-update mechanism for data."""
    def __init__(self, val=None, event_set=None, trace=False): 
        """"Create a new Signal.
        
        val       - Initialize signal with a value.
        event_set - The set of events the signal trggers.
        trace     - Should signal register for tracing or not.
        """
        
        self._tracing = trace
        self.traces = None
        self.mem = []
        self._val = val
        self._init = val
            
        self.e = event_set
        
    def blk_pop(self):
        """Pop the value from the signal queue. If the queue is empty, wait 
        for the value to become available."""
        
        if not self.mem:
            simwait(self.e.enqueued)
        
        simupdate(self)
        simwait(self.e.updated)
            
        return self._val
    
    def pop(self):
        """Pop the value from the signal queue. If the queue is empty, trigger 
        SignalQueueEmpty exception. """
        
        if self.mem:
            simupdate(self)
                        
            return self.mem[0]
        else:
            raise SignalQueueEmpty

    def blk_push(self, val):
        """Push value to signal queue only if the queue is empty. Do not 
        trigger the update."""
        
        while self.mem:
            simwait(self.e.updated)
        
        self.push(val)
           
    def push(self, val):
        """Push value to signal queue without triggering the update."""
        
        self.mem.append(val)
        if 'enqueued' in self.e:
            self.e.enqueued.trigger()
        
    def write(self, val):
        """Write a new value to the signal."""
        self._next = val
        simupdate(self)
        
    def write_after(self, val, delay):
        """Write a new value to the signal after a certain delay."""
        if delay:
            simwait(Delay(delay))

        self.write(val)
    
    def read(self):
        return self._val
        
    def _update(self):
        """Callback called by simulator if signal registered for update cycle."""
        if self.mem:
            next_val = self.mem.pop(0)
        else:
            next_val = self._next
            
        val = self._val
        
        if 'updated' in self.e:
            self.e.updated.trigger()
        
        if val != next_val:
            
            if 'changed' in self.e:
                self.e.changed.trigger()
                
            if 'event_def' in self.e:
                self.e.event_def.trigger()
                
                for _, sube in self.e.event_def.subevents.items():
                    key = sube.key
                    
                    if val.__getitem__(key) != next_val.__getitem__(key):
                        sube.trigger()

            if not val and next_val and (val is not None):
                if 'posedge' in self.e:
                    self.e.posedge.trigger()
            elif not next_val and val:
                if 'negedge' in self.e:
                    self.e.negedge.trigger()

            self._val = next_val
    