from sydpy.intfs.isig import Isig
from sydpy.process import Process
import copy
from sydpy._signal import Signal
from sydpy import ddic
from sydpy.types._type_base import convgen

class Itlm(Isig):
    _intf_type = 'itlm'

    def __init__(self, name, dtype=None, dflt=None):
        self._tlm_sinks = set()
        super().__init__(name, dtype, dflt)
    
    def _to_isig(self, other):
        if self._get_dtype() is other._get_dtype():
            self._isig_sinks.add(other)
        
    def _from_itlm(self, other):
        if self._get_dtype() is other._get_dtype():
            other._tlm_sinks.add(self)
            self._sig = Signal(val=copy.deepcopy(self._dflt), event_set = self.e)
#             self._sig = other
#             for event in self.e.search(of_type=Event):
#                 getattr(other.e, event).subscribe(event)
            
            self._sourced = True
        else:
            self.inst('_p_dtype_convgen', Process, self._pfunc_dtype_convgen, [], pargs=(other,))

    def _pfunc_tlm_dispatch(self):
        while(1):
            data_recv = self._sig.bpop()
            for s in self._tlm_sinks:
                data_conv_gen = convgen(data_recv, s._get_dtype())
                 
                try:
                    while True:
                        s.bpush(next(data_conv_gen))
                except StopIteration as e:
                    if e.value is not None:
                        s.bpush(e.value)
                        
            for s in self._isig_sinks:
                data_conv_gen = convgen(data_recv, s._get_dtype())
                try:
                    while True:
                        s <<= next(data_conv_gen)
                except StopIteration as e:
                    if e.value is not None:
                        s <<= e.value
    
    def _create_source_sig(self):
        self._sig = Signal(val=copy.deepcopy(self._dflt), event_set = self.e)
#         self.inst(Process, '_pfunc_tlm_to_tlm', self._pfunc_tlm_to_tlm)
#         Process('_pfunc_tlm_dispatch', self, self._pfunc_tlm_dispatch)
    
    def bpush(self, val):
        val = self._prep_write(val)
        self._sig.bpush(val)
        print('PUSHED: {0}'.format(self.qname))
        
    def push(self, val):
        val = self._prep_write(val)
        self._sig.push(val)
        
    def bpop(self):
        if not self._sourced:
            ddic['sim'].wait(self.e['enqueued'])
            
        return self._sig.bpop()
    
    def get_queue(self):
        if not self._sourced:
            return []
        else:
            return self._sig.get_queue()        

