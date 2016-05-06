from sydpy.component import Component#, compinit#, sydsys
from sydpy._signal import Signal
from sydpy.intfs.intf import Intf, SlicedIntf
from sydpy.intfs.isig import Isig
from sydpy.types import bit
from sydpy.process import Process
from sydpy.types._type_base import convgen

class Iseq(Intf):
    _intf_type = 'iseq'

    def __init__(self, name, dtype=None, dflt=None, clk=None):
        super().__init__(name)
        
        self._mch = None
        self._sch = None
        self._dtype = dtype
        self._dflt = dflt
        
        Isig('data', self, dtype=dtype, dflt=dflt)
        Isig('valid', self, dtype=bit, dflt=1)
        Isig('ready', self, dtype=bit, dflt=1)
        Isig('last', self, dtype=bit, dflt=0)
        Isig('_dout', self, dtype=dtype, dflt=0)
        self.c['clk'] = clk
        
#         self.inst('_p_ff_proc', Process, self._ff_proc, [self.clk.e.posedge])
#         self.inst('_p_fifo_proc', Process, self._fifo_proc, [])
        
        self.e = self.c['_dout'].e
    
    def _fifo_proc(self):
        while(1):
            self.data.bpop()
            self.last <<= (self.data.get_queue() == False)
            self.valid <<= True
            sydsys().sim.wait(self._dout.e.updated)
        
    def _ff_proc(self):
        if self.ready and self.valid:
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

#     def _connect(self, master):
#         self.con
        
    
    def _from_isig(self, other):
        self.data._connect(other)
    
    def _to_isig(self, other):
        other._connect(self._dout)
        
    def _from_itlm(self, other):
        pass
    
#     def _pfunc_tlm_to_sig(self, other):
#         data_fifo = []
#         last_fifo = []
# 
#         while(1):
#             data_recv = other.bpop()
# 
#             data_conv_gen = convgen(data_recv, self._dtype)
#             data_fifo = []
#             
#             try:
#                 while True:
#                     data_fifo.append(next(data_conv_gen))
#             except StopIteration as e:
#                 remain = e.value
#                 if remain is not None:
#                     data_fifo.append(remain)
#                     remain = None
#                 
#             for d in data_fifo:
#                 
#                 
#                 if not data_o.valid.read(False):
#                     data_o.data.next = data_fifo[0]
#                     data_o.last.next = last_fifo[0]
#                     data_o.valid.next = True
# 
#                 simwait(last_data_event)
        
    def _from_iseq(self, intf):
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
        
    def push(self, val):
        self.data.push(val)
    
    def read_next(self):
        return self._dout._next
    
    def read(self):
        return self._dout.read()
    
    def get_queue(self):
        return self._dout.get_queue()
    
    def deref(self, key):
        return SlicedIntf(self, key)
