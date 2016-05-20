from sydpy import ddic
from sydpy._signal import Signal
from sydpy._event import EventSet, Event
from sydpy.unit import Unit
from sydpy.intfs.intf import Intf, SlicedIntf
import copy
from sydpy.types._type_base import convgen, conv
from sydpy.process import Process

class Isig(Intf):
    _intf_type = 'isig'

    def __init__(self, name, dtype=None, dflt=None):
        super().__init__(name)
        self._mch = None
        self._sch = None
        self._sig = None
        self._sourced = False
        self._dtype = dtype

        if self._dtype:
            self._dflt = conv(dflt, self._dtype)
        else:
            self._dflt = dflt
            
        self._sinks = set()
#         self.inst("e", EventSet, missing_event_handle=self._missing_event)
        self.e = self.inst(EventSet, 'e', missing_event_handle=self._missing_event)
        
    def con_driver(self, intf):
        pass
    
#     def _connect(self, master):
#         if not self._sourced:
#             self._conn_to_intf(master)
    
    def _subscribe(self, intf):
        self._sinks.add(intf)
    
    def _from_isig(self, other):
        if self._get_dtype() is other._get_dtype():
#             self._sig = Signal(val=copy.deepcopy(self._dflt), event_set = self.e)
#             other._subscribe(self)
            self._sig = other
#             for event in self.e.search(of_type=Event):
#                 getattr(other.e, event).subscribe(event)
            
            self._sourced = True
        else:
            self.inst('_p_dtype_convgen', Process, self._pfunc_dtype_convgen, [], pargs=(other,))
   
    
    def _pfunc_dtype_convgen(self, other):
        while(1):
            data_recv = other.bpop()
            data_conv_gen = convgen(data_recv, self._dtype)
             
            try:
                while True:
                    self.bpush(next(data_conv_gen))
            except StopIteration as e:
                if e.value is not None:
                    self.bpush(e.value)

    def _drive(self, channel):
        self._mch = channel

    def _sink(self, channel):
        self._sch = channel
    
    def _create_source_sig(self):
        self._sig = Signal(val=copy.deepcopy(self._dflt), event_set = self.e)
    
    def _prep_write(self, val):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        if self._get_dtype():
            val = conv(val, self._get_dtype())
        
        if not self._sourced:
            self._create_source_sig()
            self._sourced = True
            
        return val
    
    def __call__(self):
        return self.read()
    
    def __ilshift__(self, other):
        self.write(other)
        return self
    
    def write(self, val):
        val = self._prep_write(val)
        self._sig.write(val)
    
    def read_next(self):
        if not self._sourced:
            if self._get_dtype():
                return conv(self._dflt, self._get_dtype())
            else:
                return self._dflt
        else:
            return self._sig._next
    
    def read(self):
        if not self._sourced:
            if self._get_dtype():
                return conv(self._dflt, self._get_dtype())
            else:
                return self._dflt
        else:
            return self._sig.read()
        
    def deref(self, key):
        return SlicedIsig(self, key)
   
    def _missing_event(self, event_set, name):
        event = self.e.inst(Event, name)
        
        if self._sourced:
            if self._sig.e is not event_set:
                getattr(self._sig.e, name).subscribe(event)

        return event
    
class SlicedIsig(Isig):
    """Provides access to the parent interface via a key."""
    def __init__(self, intf, key):
        """"Create SlicedIntf of a parent with specific key."""
        #_IntfBase.__init__(self)
        self._dtype = intf._get_dtype().deref(key)
        self._key = key
        self._parent = intf

    def _get_dtype(self):
        return self._dtype

    def __getattr__(self, name):
        if name in self._parent.c:
            return self._parent.c[name][self._key]
        else:
            return getattr(self._parent, name)
    
    def read(self):
        return self._parent.read()[self._key]
    
    def write(self, val):
        next_val = self._parent.read_next()
        next_val[self._key] = val
        return self._parent.write(next_val)
    
    def unsubscribe(self, proc, event=None):
        if event is None:
            self._parent.e.event_def[self._key].unsubscribe(proc)
        else:
            getattr(self._parent.e, event)[self._key].unsubscribe(proc)
        
    def subscribe(self, proc, event=None):
        if event is None:
            return self._parent.e.event_def[self._key].subscribe(proc)
        else:
            getattr(self._parent.e, event)[self._key].subscribe(proc)
            
class Csig(Isig):
    pass
