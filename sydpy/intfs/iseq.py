from sydpy.component import Component#, compinit#, sydsys
from sydpy._signal import Signal
from sydpy.intfs.intf import Intf, SlicedIntf
from sydpy.intfs.isig import Isig
from sydpy.types import bit
from sydpy.process import Process
from sydpy.types._type_base import convgen
from ddi.ddi import ddic
from sydpy.intfs.itlm import Itlm
from sydpy._event import EventSet

class Iseq(Intf):
    _intf_type = 'iseq'

    def __init__(self, name, dtype=None, dflt=None, clk=None):
        super().__init__(name)
        
        self._mch = None
        self._sch = None
        self._dtype = dtype
        self._dflt = dflt
        
        self.inst(Isig, 'data', dtype=dtype, dflt=dflt)
        self.inst(Isig, 'valid', dtype=bit, dflt=1)
        self.inst(Isig, 'ready', dtype=bit, dflt=1)
        self.inst(Isig, 'last', dtype=bit, dflt=0)
#         self.inst(Isig, '_dout', dtype=dtype, dflt=0)
        
        self.c['clk'] = clk
        
        self.e = self.inst(EventSet, 'e')
        self._dout = Signal(val=dtype(dflt), event_set=self.e)
        
        self.inst(Process, '_p_ff_proc', self._ff_proc, senslist=[self.c['clk'].e['posedge']])
#        self.inst(Process, '_p_fifo_proc', self._fifo_proc, senslist=[])
        
#         self.e = self._dout.e
        self._itlm_sinks = set()
    
    def _fifo_proc(self):
        while(1):
            self.c['data'].bpop()
            self.c['last'] <<= (self.c['data'].get_queue() == False)
            self.c['valid'] <<= True
            ddic['sim'].wait(self.e['updated'])
        
    def _ff_proc(self):
        if (self.c['ready'] and self.c['valid'] and
            all([i.empty() for i in self._itlm_sinks])):
            
            self._dout.write(self.c['data'].read())
            for i in self._itlm_sinks:
                i.push(self.c['data'])
        
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
        self.c['data']._connect(other)
    
    def _to_isig(self, other):
        other._connect(self._dout)
    
    def _to_itlm(self, other):
        self._itlm_sinks.add(other)
    
    def _from_itlm(self, other):
        sig = other._subscribe(self, self._get_dtype())
        self.inst(Itlm,  'data', dtype=self._get_dtype(), dflt=sig.read())
        self.c['data']._sig = sig
        self.c['data']._sig.e = self.c['data'].e
        self.c['data']._sourced = True
        
        self.inst(Process, '_p_fifo_proc', self._fifo_proc, senslist=[])
    
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
        self.c['data'].write(val)
        
    def push(self, val):
        self.c['data'].push(val)
    
    def read_next(self):
        return self._dout._next
    
    def read(self):
        return self._dout.read()
    
    def get_queue(self):
        return self._dout.get_queue()
    
    def deref(self, key):
        return SlicedIntf(self, key)
