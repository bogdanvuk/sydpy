from sydpy import compinit, ddic
from sydpy._signal import Signal
from sydpy._event import EventSet, Event
from sydpy.unit import Unit
from sydpy.intfs.intf import Intf, SlicedIntf
import copy
from sydpy.types._type_base import convgen
from sydpy.process import Process

class isig(Intf):
    _intf_type = 'isig'

    @compinit
    def __init__(self, name, parent, dtype, dflt=None):
        super().__init__(name, parent)
        
        self._mch = None
        self._sch = None
        self._sig = None
        self._sourced = False
        self._dtype = dtype
        self._dflt = self._dtype.conv(dflt)
        self._sinks = set()
#         self.inst("e", EventSet, missing_event_handle=self._missing_event)
        self.e = EventSet('e', self, missing_event_handle=self._missing_event)
        
    def con_driver(self, intf):
        pass
    
#     def _connect(self, master):
#         if not self._sourced:
#             self._conn_to_intf(master)
        
    def _from_isig(self, other):
        if self._get_dtype() is other._get_dtype():
            self._sig = other
            for event in self.e.search(of_type=Event):
                getattr(other.e, event).subscribe(event)
            
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
    
    def _prep_write(self, val):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        val = self._get_dtype().conv(val)
        
        if not self._sourced:
            self._sig = Signal(val=copy.deepcopy(self._dflt), event_set = self.e)
            self._sourced = True
            
        return val
    
    def bpush(self, val):
        val = self._prep_write(val)
        self._sig.bpush(val)
        
    def push(self, val):
        val = self._prep_write(val)
        self._sig.push(val)
    
    def write(self, val):
        val = self._prep_write(val)
        self._sig.write(val)
    
    def read_next(self):
        if not self._sourced:
            return copy.deepcopy(self._dflt)
        else:
            return self._sig._next
    
    def read(self):
        if not self._sourced:
            return copy.deepcopy(self._dflt)
        else:
            return self._sig.read()
        
    def bpop(self):
        if not self._sourced:
            ddic['sim'].wait(self.e['enqueued'])
            
        return self._sig.bpop()
    
    def deref(self, key):
        return SlicedIntf(self, key)
    
    def get_queue(self):
        if not self._sourced:
            return []
        else:
            return self._sig.get_queue()
    
    def _missing_event(self, event_set, name):
        event = Event(name, self.e)
        
        if self._sourced:
            if self._sig.e is not event_set:
                getattr(self._sig.e, name).subscribe(event)

        return event