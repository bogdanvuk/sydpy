from sydpy.component import Component, compinit
from sydpy._signal import Signal
from sydpy._event import EventSet
from sydpy.unit import Unit
from sydpy.intfs.intf import Intf, SlicedIntf

class isig(Intf):
    _intf_type = 'isig'

    @compinit
    def __init__(self, dtype, dflt, **kwargs):
        self._mch = None
        self._sch = None
        self._sig = None
        self._dtype = dtype
        self._dflt = self._dtype.conv(dflt)
        self._sinks = set()
        self.e = EventSet(missing_event_handle=self._missing_event)
        
    def con_driver(self, intf):
        pass
    
    def _get_dtype(self):
        return self._dtype
    
    def _find_sources(self):
        if self._sch:
            if self._sig is None:
                self.conn_to_intf(self._sch.master)
            
            if self._sig is not None:
                return True
            else:
                return False
        else:
            return True
        
    def _add_source(self, intf):
        self._sig = intf
        for event in self.e:
            getattr(intf.e, event).subscribe(event)
            
        self.e = intf.e

    def _drive(self, channel):
        self._mch = channel

    def _sink(self, channel):
        self._sch = channel
    
    def write(self, val, keys=None):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        val = self._dtype.conv(val)
        
        if self._sig is None:
            self._sig = Signal(val=self._dflt, event_set = self.e)
                    
        self._sig.write(val)
    
    def read_next(self):
        if self._sig is None:
            return self._dflt
        else:
            return self._sig._next
    
    def read(self):
        if self._sig is None:
            return self._dflt
        else:
            return self._sig.read()
    
    def deref(self, key):
        return SlicedIntf(self, key)
