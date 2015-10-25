from sydpy.component import Component, compinit
from sydpy._signal import Signal
from sydpy._event import EventSet
from sydpy.unit import Unit
from sydpy.intfs.intf import Intf

class isig(Component, Intf):
    _intf_type = 'isig'
#     def __init__(self, parent, name, dtype, dflt):
#         Unit.__init__(self, name)
#         self.dtype = dtype
#         self.dflt = dflt

    @compinit
    def __init__(self, name, dtype, dflt):
        self._mch = None
        self._sch = None
        self._sig = None
        self.dtype = dtype
        self.dflt = dflt
        
    def con_driver(self, intf):
        pass
    
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
            self._sig = Signal(val=self.dtype.conv(self.dflt))
            self.e = self._sig.e
    
    def write(self, val, keys=None):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        val = self.dtype.conv(val)
        
        self._sig.write(val)
    
    def read(self):
        return self._sig.read()