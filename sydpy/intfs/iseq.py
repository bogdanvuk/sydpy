from sydpy.component import Component#, compinit#, sydsys
from sydpy._signal import Signal
from sydpy.intfs.intf import Intf, SlicedIntf
from sydpy.intfs.isig import Isig, Csig
from sydpy.types import bit
from sydpy.process import Process
from sydpy.types._type_base import convgen
from ddi.ddi import ddic
from sydpy.intfs.itlm import Itlm
from sydpy._event import EventSet
from sydpy.types.array import Array
from enum import Enum

class FlowCtrl(Enum):
    both = 1
    valid = 2
    ready = 3
    none = 4

class Iseq(Intf):
    _intf_type = 'iseq'
    feedback_subintfs = ['ready']

    def __init__(self, name, dtype=None, dflt=None, clk=None, flow_ctrl=FlowCtrl.both, trans_ctrl=True):
        super().__init__(name)
        
        self._mch = None
        self._sch = None
        self._dtype = dtype
        self._dflt = dflt
        
        self.inst(Isig, 'data', dtype=dtype, dflt=dflt)
        if flow_ctrl == FlowCtrl.both or flow_ctrl == FlowCtrl.valid:
            self.inst(Isig, 'valid', dtype=bit, dflt=0)
        else:
            self.inst(Csig, 'valid', dtype=bit, dflt=1)
        
        if flow_ctrl == FlowCtrl.both or flow_ctrl == FlowCtrl.ready:
            self.inst(Isig, 'ready', dtype=bit, dflt=0)
        else:
            self.inst(Csig, 'ready', dtype=bit, dflt=1)
    
        if trans_ctrl:        
            self.inst(Isig, 'last', dtype=bit, dflt=1)
        else:
            self.inst(Csig, 'last', dtype=bit, dflt=1)
#         self.inst(Isig, '_dout', dtype=dtype, dflt=0)
        
        self.clk = clk
        self.flow_ctrl = flow_ctrl
        self.trans_ctrl = trans_ctrl
        self.inst(EventSet, 'e')
        self._dout = Signal(val=dtype(dflt), event_set=self.e)
        
        self.inst(Process, '_p_ff_proc', self._ff_proc, senslist=[self.clk.e.posedge])
      
#        self.inst(Process, '_p_fifo_proc', self._fifo_proc, senslist=[])
        
#         self.e = self._dout.e
        self._itlm_sinks = set()
        self._iseq_sinks = set()
        self._itlm_data = []
    
    def _fifo_proc(self, srcsig):
        data = []
        while(1):
                 
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


    def _ff_proc(self):
        if self.name == 'top/unpack_lookup/sout0':
            pass
#             print('COSIM DIN: ', self.data())
#             print('COSIM VALID: ', self.last())
#             print('COSIM LAST: ', self.valid())
#             print('COSIM READY: ', self.ready())
            
        if (self.ready() and self.valid()): # and
            #all([i.empty() for i in self._itlm_sinks])):
            
            self._dout.write(self.data())
            
            if not self._itlm_data:
                for i in self._itlm_sinks:
                    self._itlm_data.append(Array(self._get_dtype())())
            
            for i, intf in enumerate(self._itlm_sinks):
                self._itlm_data[i].append(self.data())
                
            if self.last():
                for i, intf in enumerate(self._itlm_sinks):
                    for d, _ in convgen(self._itlm_data[i], intf._get_dtype()):
                        intf.push(d)
                        
                self._itlm_data = []
    
    def _p_ready_proc(self):
        senslist = [s.ready for s in self._iseq_sinks]
        while(1):
            ddic['sim'].wait(*senslist)
#             
            if self.name == 'top/unpack_lookup/sout0':
                pass
        
            for s in self._iseq_sinks:
                if not s.ready():
                    self.ready <<= False
                    break;
            else:
                self.ready <<= True
    
    def con_driver(self, intf):
        pass
    
    def _get_dtype(self):
        return self._dtype
    
    def _from_isig(self, other):
        self.data._connect(other)
    
    def _to_isig(self, other):
        other._connect(self._dout)
    
    def _to_itlm(self, other):
        self._itlm_sinks.add(other)
        self.ready._dflt = 1
#         self._ready_src_events.add(other.)
#         if '_p_ready_proc' not in self.c:
#             self.inst(Process, '_p_ready_proc', self._ready_proc, senslist=[])
    
    def _from_itlm(self, other):
        sig = other._subscribe(self, self._get_dtype())
        self.valid._dflt = 0
        self.last._dflt = 0
        self.inst(Process, '', self._fifo_proc, senslist=[], pkwargs=dict(srcsig=sig))
        
    def _to_iseq(self, other):
        self._iseq_sinks.add(other)
        if (self.flow_ctrl == FlowCtrl.both or self.flow_ctrl == FlowCtrl.ready) and \
           ('_p_ready_proc' not in self.c):
            self.inst(Process, '_p_ready_proc', self._p_ready_proc, senslist=[])
        
        self.valid >> other.valid
        self.last >> other.last
        self.data >> other.data
    
    def _drive(self, channel):
        self._mch = channel
        
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
