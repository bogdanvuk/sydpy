from sydpy.component import Component, compinit
from sydpy._signal import Signal
from sydpy._event import EventSet, Event
from sydpy.unit import Unit
from sydpy.intfs.intf import Intf, SlicedIntf
import copy

class isig(Intf):
    _intf_type = 'isig'

    @compinit
    def __init__(self, dtype, dflt=None, **kwargs):
        self._mch = None
        self._sch = None
        self._sig = None
        self._sourced = False
        self._dtype = dtype
        self._dflt = self._dtype.conv(dflt)
        self._sinks = set()
        self.inst("e", EventSet, missing_event_handle=self._missing_event)
        
    def con_driver(self, intf):
        pass
    
    def _get_dtype(self):
        return self._dtype
    
#     def _connect(self, master):
#         if not self._sourced:
#             self._conn_to_intf(master)
        
    def _from_isig(self, intf):
        self._sig = intf
        for event in self.e.search(of_type=Event):
            getattr(intf.e, event).subscribe(event)
        
        self._sourced = True
        
#         self.e = intf.e

    def _drive(self, channel):
        self._mch = channel

    def _sink(self, channel):
        self._sch = channel
    
    def write(self, val):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        val = self._dtype.conv(val)
        
        if not self._sourced:
            self._sig = Signal(val=copy.deepcopy(self._dflt), event_set = self.e)
            self._sourced = True
                    
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
    
    def deref(self, key):
        return SlicedIntf(self, key)
    
    def _missing_event(self, event_set, name):
        event = self.e.inst(name, Event)
        
        if self._sourced:
            if self._sig.e is not event_set:
                getattr(self._sig.e, name).subscribe(event)

        return event