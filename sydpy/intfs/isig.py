from sydpy.component import Component, compinit
from sydpy._signal import Signal
from sydpy._event import EventSet
from sydpy.unit import Unit
from sydpy.intfs.intf import Intf, SlicedIntf

class isig(Component, Intf):
    _intf_type = 'isig'

    @compinit
    def __init__(self, dtype, dflt, **kwargs):
        Intf.__init__(self)
        self._mch = None
        self._sch = None
        self._sig = None
        self._dtype = dtype
        self._dflt = dflt
        
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
        self._sig = intf._sig
        self.e = self._sig.e
    
    def _gen_drivers(self):
        if self._mch:
            self._sig = Signal(val=self._dtype.conv(self._dflt))
            self.e = self._sig.e
    
    def write(self, val, keys=None):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        val = self._dtype.conv(val)
        
        self._sig.write(val)
    
    def read(self):
        return self._sig.read()
    
    def deref(self, key):
        return SlicedIntf(self, key)
