'''
Created on Oct 4, 2014

@author: bvukobratovic
'''
from fpyga.event import Event, EventSet
from fpyga.tracing import VCDTrace
from fpyga.component import Component
from fpyga._delay import Delay

from copy import copy, deepcopy
from fpyga._intbv import intbv
from fpyga._bin import bin
from fpyga._enum import EnumItemType
from fpyga import simwait
# import inject

import operator 
from ._injector import RequiredFeature  # @UnresolvedImport
from .fpy_object import FpyObject

from enum import Enum

class SignalQueueEmpty(Exception):
    pass

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

class Signal(Component):
    '''
    classdocs
    '''

#     _simulator = inject.attr(Simulator)
    _simulator = RequiredFeature('Simulator')
    
#     __slots__ = ('_next', '_val', '_type', '_init',
#              '_eventWaiters', '_posedgeWaiters', '_negedgeWaiters',
#              '_code', '_tracing', '_nrbits', '_checkVal', 
#              '_setNextVal', '_copyVal2Next', '_printVcd', 
#              '_driven' ,'_read', '_name', '_used', '_inList',
#              '_waiter', 'toVHDL', 'toVerilog', '_slicesigs',
#              '_numeric', 'updated', 'change', 'posedge', 'negedge', 'event_def'
#             )

    def __ilshift__(self, val):
        self.write(val)
        return self

    def blk_write(self, val, delay=0):
        if self.mem_type == SignalMem.queue:
            if isinstance(val, Signal):
                val = val._val
             
            if isinstance(val, (bool, int, float, str)):
                next_val = val
            else:
                next_val = deepcopy(val)
             
            if delay:
                simwait(Delay(delay))
             
            self.mem.append(next_val)
            self.e.enqueued.trigger()
             
            if self.qstate in ('idle', 'update'):
                simwait(self.e.requested)
            else:   
                self.qstate = 'update'
                self._next = next_val
                self._simulator.update_pool.add(self)
                
#             elif self.qstate == 'subs':
#                 self.qstate = 'update'
#                 self._next = next_val
#                 self._simulator.update_pool.add(self)
                
            simwait(self.e.updated)
            
        else:
                        
            if delay:
                self.write_after(val, delay)
            else:
                self.write(val)

    def write(self, next_val, delay=0):
        
#         if isinstance(val, Signal):
#             val = val._val
#             
#         if isinstance(val, (bool, int, float, str)):
#             next_val = val
#         else:
#             next_val = deepcopy(val)

#         next_val = val
            
        if self.stype == SignalType.signal:
            self._next = next_val
            self._simulator.update_pool.add(self)
        elif self.stype == SignalType.queue:
            self.mem.append(next_val)
            if self.qstate in ('idle', 'update'):
                self.e.enqueued.trigger()
            elif self.qstate == 'subs':
                self._next = next_val
                self._simulator.update_pool.add(self)
                self.qstate = 'update'
            
        elif self.stype == SignalType.delta_queue:
            if not self.mem:
                self._next = next_val
                 
                self._simulator.update_pool.add(self)
                 
            self.mem.append(next_val)
            
        
    def write_after(self, val, delay):
        if delay:
            simwait(Delay(delay))

        self.write(val)
    
    def read(self):
        return self._val
    
    def acquire(self):
        if (self.mem_type == SignalMem.queue) and (self.mem):
            val = self.blk_read()
            return val
        elif (self.mem_type == SignalMem.queue):
            raise SignalQueueEmpty
        else:
            val = self.read()
    
    def blk_read(self):
        if self.mem_type in (SignalMem.queue, SignalMem.delta_queue):
#             try:
            if self.mem and self.qstate == 'idle':
                self.e.requested.trigger()
                self._next = self.mem[0]
                self._simulator.update_pool.add(self)
                self.qstate = 'update'
            else:
                self.e.requested.trigger()
                self.qstate = 'subs'
#             except:
#                 pass
        
        simwait(self.e.updated)
            
#             if self.qstate == 'subs':
#                 if self.mem:
#                     self.qstate = 'update'
#                     self._next = self.mem[0]
#                     self._simulator.update_pool.add(self)

#         yield self.e.updated
        return self._val
        
    def _update(self):
        val, next_val = self._val, self._next
        
        if self.stype in (SignalType.queue, SignalType.delta_queue):
            try:
                self.mem.pop(0)
            except:
                pass
            self.qstate = 'idle'
            
            if 'event_def' in self.e.events:
                self.e.event_def.trigger()
        
        if 'updated' in self.e.events:
            self.e.updated.trigger()
            
        if val != next_val:
            self.trace_val_updated = True
            
            if 'changed' in self.e.events:
                self.e.changed.trigger()
                
            if self.stype == SignalType.signal:
                if 'event_def' in self.e.events:
                    self.e.event_def.trigger()
                    
                    for _, sube in self.e.event_def.subevents.items():
                        key = sube.key
                        
                        if val.__getitem__(key) != next_val.__getitem__(key):
                            sube.trigger()

            if not val and next_val and (val is not None):
                if 'posedge' in self.e.events:
                    self.e.posedge.trigger()
            elif not next_val and val:
                if 'negedge' in self.e.events:
                    self.e.negedge.trigger()

            self._val = next_val

#             if val is None:
#                 self.set_val(next_val)
#             elif next_val is None:
#                 self._val = None
#             elif isinstance(val, intbv):
#                 self._val = intbv(int(next_val), self._val._nrbits)
#             elif isinstance(val, (int, EnumItemType)):
#                 self._val = next_val
# #             elif isinstance(next, FpyObject):
# #                 self._val = next
#             else:
# #                 self.set_val(next_val)
#                 self._val = deepcopy(next_val)
                
#     def set_val(self, val):
#         if val is None:
#             self._init = None
#             self._val = None
#             self._next = None
#         else:
#             self._init = deepcopy(val)
#             self._val = deepcopy(val)
#             self._next = deepcopy(val)
#             
#             if isinstance(val, bool):
#                 self._type = bool
#     #             self._setNextVal = self._setNextBool
#                 self.trace_val = self._printVcdBit
#                 self._trace_print_type = 'integer'
#                 self._trace_type = 'reg'
#                 self._nrbits = 1
#             elif isinstance(val, int):
#                 self._type = int
#     #             self._setNextVal = self._setNextInt
# #                 self._trace_print_type = 'integer'
# #                 self._trace_type = 'reg'
#                 self.trace_val = self._printVcdStr
#                 self._trace_print_type = 'string'
#                 self._trace_type = 'real'
#             elif isinstance(val, intbv):
#                 self._type = intbv
#                 self._min = val._min
#                 self._max = val._max
#                 self._nrbits = val._nrbits
#     #             self._setNextVal = self._setNextIntbv
#                 if self._nrbits:
#                     self.trace_val = self._printVcdVec
#                     self._trace_print_type = 'vector'
#                     self._trace_type = 'reg'
#                 else:
#                     self.trace_val = self._printVcdHex
#                     self._trace_print_type = 'string'
#                     self._trace_type = 'real'
#             else:
#                 self._type = type(val)
#     #             if isinstance(init, EnumItemType):
#     #                 self._setNextVal = self._setNextNonmutable
#     #             else:
#     #                 self._setNextVal = self._setNextMutable
#                 if hasattr(val, '_nrbits'):
#                     self._nrbits = val._nrbits
#                     
#             if self._tracing and (not self.traces):
#                 
#                 self.trace_val_updated = True
#                 
#                 if val is not None:
#                     val_str = self.trace_val(self._init)
#                 else:
#                     val_str = None
#                  
#                 self.traces = VCDTrace(self.caption, self, init=val_str, width=self._nrbits, trace_type=self._trace_type, print_type=self._trace_print_type)

#     def missing_event(self, event_set, event):
#         e = Event(self.qualified_name + '.' + event)
#         event_set.add({event:e})
#        
#         return e

#     @property
#     def event_def(self):
#         if self.mem_type == SignalMem.signal:
#             return self.e.changed
#         else:
#             return self.e.updated
     
    def __init__(self, name, parent, val=None, caption=None, stype=SignalType.signal, event_set=None, trace=False):
        '''
        Constructor
        '''
        
        Component.__init__(self, name, parent)
        
        self._name = name
        self.stype = stype
        self._tracing = trace
        self.traces = None
        self.mem = []
        self._val = val
        self._init = val
        self._next = val
        
        if caption is None:
            self.caption = name
        else:
            self.caption = caption
            
        self.e = event_set
        
        if self._tracing:
                
            self.trace_val_updated = True
            
            if val is not None:
                val_str = str(self._init)
            else:
                val_str = None
             
            self.traces = VCDTrace(self.caption, self, init=val_str)


#         self.trace_val = self._printVcdStr        
#         self._trace_print_type = 'string'
#         self._trace_type = 'real'
#         self._nrbits = None
        
        self.qstate = 'idle'
        
    def trace_val(self, name):
        if self.trace_val_updated:
            if self._val is not None:
                self.trace_val_old = self._val
            else:
                self.trace_val_old = None
                
            self.trace_val_updated = False
        
        return self.trace_val_old
          
#         self.set_val(val)
#         
#         if val is not None:
#             self._simulator.update_pool.add(self)
        
#         self.e = EventSet(missing_event_handle=self.missing_event)
    
#     # set next methods
#     def _setNextBool(self, val):
#         if not val in (0, 1):
#             raise ValueError("Expected boolean value, got %s (%s)" % (repr(val), type(val)))
#         self._next = val
# 
#     def _setNextInt(self, val):
#         if not isinstance(val, (int, intbv)):
#             raise TypeError("Expected int or intbv, got %s" % type(val))
#         self._next = val
# 
#     def _setNextIntbv(self, val):
#         if isinstance(val, intbv):
#             val = val._val
#         elif not isinstance(val, int):
#             raise TypeError("Expected int or intbv, got %s" % type(val))
# #        if self._next is self._val:
# #            self._next = type(self._val)(self._val)
#         self._next._val = val
#         self._next._handleBounds()
# 
#     def _setNextNonmutable(self, val):
#         if not isinstance(val, self._type):
#             raise TypeError("Expected %s, got %s" % (self._type, type(val)))
#         self._next = val    
#         
#     def _setNextMutable(self, val):
#         if not isinstance(val, self._type):
#             raise TypeError("Expected %s, got %s" % (self._type, type(val)))
#         self._next = deepcopy(val)         

    # vcd print methods
#     def _printVcdStr(self, name):
#         if self.trace_val_updated:
#             if self._val is not None:
#                 self.trace_val_old = str(self._val)
#             else:
#                 self.trace_val_old = ""
#                 
#             self.trace_val_updated = False
#         
#         return self.trace_val_old
#         
#     def _printVcdHex(self, name):
#         if self.trace_val_updated:
#             self.trace_val_old = hex(self._val)
#             self.trace_val_updated = False
#             
#         return self.trace_val_old
#         
# 
#     def _printVcdBit(self, name):
#         if self.trace_val_updated:
#             self.trace_val_updated = False
#             if self._val:
#                 self.trace_val_old = str(1)
#             else:
#                 self.trace_val_old = str(0)
#             
#         return self.trace_val_old        
# 
#     def _printVcdVec(self, name):
#         if self.trace_val_updated:
#             self.trace_val_old = bin(self._val, self._nrbits)
#             self.trace_val_updated = False
#             
#         return self.trace_val_old
        
    ### operators for which delegation to current value is appropriate ###
        
#     def __hash__(self):
#         return hash(self)
#         raise TypeError("Signals are unhashable")
        
    
    def __nonzero__(self):
        if self._val:
            return 1
        else:
            return 0
 
    # length
    def __len__(self):
#         return self._nrbits
        if not isinstance(self._val, str):
            try:
                return len(self._val)
            except:
                return 1
        else:
            return 1
 
    # indexing and slicing methods
 
    def __getitem__(self, key):
        return self._val[key]
         
    # integer-like methods
 
    def __add__(self, other):
        if isinstance(other, Signal):
            return self._val + other._val
        else:
            return self._val + other
    def __radd__(self, other):
        return other + self._val
     
    def __sub__(self, other):
        if isinstance(other, Signal):
            return self._val - other._val
        else:
            return self._val - other
    def __rsub__(self, other):
        return other - self._val
 
    def __mul__(self, other):
        if isinstance(other, Signal):
            return self._val * other._val
        else:
            return self._val * other
    def __rmul__(self, other):
        return other * self._val
 
    def __div__(self, other):
        if isinstance(other, Signal):
            return self._val / other._val
        else:
            return self._val / other
    def __rdiv__(self, other):
        return other / self._val
     
    def __truediv__(self, other):
        if isinstance(other, Signal):
            return operator.truediv(self._val, other._val)
        else:
            return operator.truediv(self._val, other)
    def __rtruediv__(self, other):
        return operator.truediv(other, self._val)
     
    def __floordiv__(self, other):
        if isinstance(other, Signal):
            return self._val // other._val
        else:
            return self._val // other
    def __rfloordiv__(self, other):
        return other //  self._val
     
    def __mod__(self, other):
        if isinstance(other, Signal):
            return self._val % other._val
        else:
            return self._val % other
    def __rmod__(self, other):
        return other % self._val
 
    # XXX divmod
     
    def __pow__(self, other):
        if isinstance(other, Signal):
            return self._val ** other._val
        else:
            return self._val ** other
    def __rpow__(self, other):
        return other ** self._val
 
    def __lshift__(self, other):
        if isinstance(other, Signal):
            return self._val << other._val
        else:
            return self._val << other
    def __rlshift__(self, other):
        return other << self._val
             
    def __rshift__(self, other):
        if isinstance(other, Signal):
            return self._val >> other._val
        else:
            return self._val >> other
    def __rrshift__(self, other):
        return other >> self._val
            
    def __and__(self, other):
        if isinstance(other, Signal):
            return self._val & other._val
        else:
            return self._val & other
    def __rand__(self, other):
        return other & self._val
 
    def __or__(self, other):
        if isinstance(other, Signal):
            return self._val | other._val
        else:
            return self._val | other
    def __ror__(self, other):
        return other | self._val
     
    def __xor__(self, other):
        if isinstance(other, Signal):
            return self._val ^ other._val
        else:
            return self._val ^ other
    def __rxor__(self, other):
        return other ^ self._val
     
    def __neg__(self):
        return -self._val
 
    def __pos__(self):
        return +self._val
 
    def __abs__(self):
        return abs(self._val)
 
    def __invert__(self):
        return ~self._val
         
    # conversions
     
    def __int__(self):
        return int(self._val)
         
    def __float__(self):
        return float(self._val)
     
    def __oct__(self):
        return oct(self._val)
     
    def __hex__(self):
        return hex(self._val)
     
    def __index__(self):
        return self._val.__index__()
 
    def __hash__(self):
#         return self._val.__hash__()
        return object.__hash__(self.qualified_name)
 
    # comparisons
    def __eq__(self, other):
        return self._val == other 
    def __ne__(self, other):
        return self._val != other 
    def __lt__(self, other):
        return self._val < other
    def __le__(self, other):
        return self._val <= other
    def __gt__(self, other):
        return self._val > other
    def __ge__(self, other):
        return self._val >= other
 
 
    # method lookup delegation
#     def __getattr__(self, attr):
#         return getattr(self._val, attr)
 
    # representation 
    def __str__(self):
        return self.qualified_name + "(" + repr(self._val) + ")"
#         if self._name:
#             return self._name
#         else:
#             return str(self._val)
 
    def __repr__(self):
        return "Signal(" + repr(self._val) + ")"
 
    def _toVerilog(self):
        return self._name
 
    # augmented assignment not supported
    def _augm(self):
        raise TypeError("Signal object doesn't support augmented assignment")
 
    __iadd__ = __isub__ = __idiv__ = __imul__ = __ipow__ = __imod__ = _augm
    __ior__ = __iand__ = __ixor__ = __irshift__ = _augm
#     __ior__ = __iand__ = __ixor__ = __irshift__ = __ilshift__ = _augm
 
    # index and slice assignment not supported
    def __setitem__(self, key, val):
#         next_val = self._val
#         next_val[key] = val
#         self.write(next_val)
        raise TypeError("Signal object doesn't support item/slice assignment")
    