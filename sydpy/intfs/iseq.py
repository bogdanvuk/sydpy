from sydpy.component import Component, compinit
from sydpy._signal import Signal
from sydpy.intfs.intf import Intf, SlicedIntf
from sydpy.intfs.isig import isig
from sydpy.types import bit
from sydpy.process import Process

class iseq(Component):
    _intf_type = 'iseq'

    @compinit
    def __init__(self, dtype, dflt, **kwargs):
        self._mch = None
        self._sch = None
        self._dtype = dtype
        self._dflt = dflt
        
        self.inst('data', isig, dtype=dtype, dflt=dflt)
        self.inst('valid', isig, dtype=bit, dflt=1)
        self.inst('ready', isig, dtype=bit, dflt=1)
        self.inst('last', isig, dtype=bit, dflt=0)
        self.inst('clk', isig, dtype=bit, dflt=0)
        self.inst('_dout', isig, dtype=dtype, dflt=0)
        self.inst('_p_ff_proc', Process, self._ff_proc, [self.clk.e.posedge])
        
        self.e = self._dout.e
        
    def _ff_proc(self):
        if self.valid and self.ready:
            self._dout <<= self.data
        
    def con_driver(self, intf):
        pass
    
    def _get_dtype(self):
        return self._dtype
    
#     def _find_sources(self):
#         if self._sch:
#             if self._sig is None:
#                 self.conn_to_intf(self._sch.master)
#             
#             if self._sig is not None:
#                 return True
#             else:
#                 return False
#         else:
#             return True
        
    def _add_source(self, intf):
        self._sig = intf._sig
        self.e = self._sig.e
    
    def _drive(self, channel):
        self._mch = channel
        self._dout._drive(channel)
#         self._sig = Signal(val=self._dtype.conv(self._dflt))
#         self.e = self._sig.e
        
    def _sink(self, channel):
        self._sch = channel
    
    def write(self, val):
        self.data.write(val)
    
    def read_next(self):
        return self._dout._next
    
    def read(self):
        return self._dout.read()
    
    def deref(self, key):
        return SlicedIntf(self, key)
