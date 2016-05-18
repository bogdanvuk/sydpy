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
    feedback_subintfs = ['ready']

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
        
        self.clk = clk
        
        self.inst(EventSet, 'e')
        self._dout = Signal(val=dtype(dflt), event_set=self.e)
        
        self.inst(Process, '_p_ff_proc', self._ff_proc, senslist=[self.clk.e.posedge])
#        self.inst(Process, '_p_fifo_proc', self._fifo_proc, senslist=[])
        
#         self.e = self._dout.e
        self._itlm_sinks = set()
    
    def __call__(self):
        return self.read()
    
    def _fifo_proc(self, srcsig):
        data = []
        while(1):
            
#             while (not self.ready()) or (not srcsig.mem):
#                 if not self.ready():
#                     ddic['sim'].wait(self.ready.e.changed)
#                  
            if not srcsig.mem:
                ddic['sim'].wait(srcsig.e.enqueued)
            
            if (not data) and (srcsig.mem):
                for val in srcsig.mem:
                    for d, _ in convgen(val, self._get_dtype()):
                        data.append(d)
                        
                fifo_reserved_cnt = len(srcsig.mem)
                        
            for i, d in enumerate(data):
                self.data <<= d 
                self.valid <<= True
                self.last <<= (i == (len(data)-1))
                ddic['sim'].wait(self._dout.e.updated)

            for _ in range(fifo_reserved_cnt):
                srcsig.pop()
            data = []
            fifo_reserved_cnt = 0
                
            self.valid <<= False

#             self.ready <<= True
#             ddic['sim'].wait(srcsig.e.enqueued, srcsig.e.updated)                
# #                 for d, _ in convgen(val, self._dtype.deref(keys[-1])):
# #                     data.append(d)
#                     
#             for i, d in enumerate(data):
#                 self.data <<= d
# #                 data_sig = self.data
# #                 for k in keys:
# #                     data_sig = data_sig[k]
# #                         
# #                 data_sig <<= d
#                 self.last <<= (i == (len(data) - 1))
#                 self.valid <<= True
#             ddic['sim'].wait(self.clk.e.posedge)
        
    def _ff_proc(self):
        if self.name == 'top/jesd_packer/din':
            print('COSIM DIN: ', self.data())
            print('COSIM VALID: ', self.last())
            print('COSIM LAST: ', self.valid())
            print('COSIM READY: ', self.ready())
            
        if (self.ready() and self.valid() and
            all([i.empty() for i in self._itlm_sinks])):
            
            self._dout.write(self.data())
            for i in self._itlm_sinks:
                i.push(self.data)
                
#         self.last <<= False
#         self.valid <<= False
        
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
    
    def _to_itlm(self, other):
        self._itlm_sinks.add(other)
    
    def _from_itlm(self, other):
        sig = other._subscribe(self, self._get_dtype())
#         self.inst(Itlm,  'data', dtype=self._get_dtype(), dflt=sig.read())
#         self.data._sig = sig
#         self.data._sig.e = self.data.e
#         self.data._sourced = True
        self.valid._dflt = 0
        self.last._dflt = 0
        self.inst(Process, '', self._fifo_proc, senslist=[], pkwargs=dict(srcsig=sig))
    
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
        return SlicedIseq(self, key)

class SlicedIseq(Iseq):
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
            if name == 'data':
                return self._parent.c[name][self._key]
            else:
                return self._parent.c[name]
        else:
            return getattr(self._parent, name)

    def _from_itlm(self, other):
        self._parent.valid._dflt = 0
        self._parent.last._dflt = 0
        super()._from_itlm(other)
    
    def read(self):
        return self._parent.read()[self._key]
    
    def write(self, val):
        next_val = self._parent.read_next()
        for k in self._key[:-1]:
            next_val = next_val[k]
            
        next_val[self._key[-1]] = val
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
