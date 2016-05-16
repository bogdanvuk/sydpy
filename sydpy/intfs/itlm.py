from sydpy.intfs.isig import Isig
from sydpy.process import Process
import copy
from sydpy._signal import Signal
from sydpy import ddic
from sydpy.types._type_base import convgen
from sydpy._event import Event, EventSet

class Itlm(Isig):
    _intf_type = 'itlm'

    def __init__(self, name, dtype=None, dflt=None):
        self._tlm_sinks = {}
        super().__init__(name, dtype, dflt)
    
    def _to_isig(self, other):
        if self._get_dtype() is other._get_dtype():
            self._isig_sinks.add(other)
        
    def _subscribe(self, intf, dtype=None):
        sig = Signal(val=copy.deepcopy(self._dflt), event_set=EventSet('e'))
#         if dtype is None:
#             dtype = self._get_dtype()
#         sig._dtype = dtype
        self._sinks.add(sig)
        
#         if self._sourced and ('_pfunc_tlm_dispatch' not in self.c):
#             self.inst(Process, '_pfunc_tlm_dispatch', self._pfunc_tlm_dispatch)
        
        return sig
        
    def _from_itlm(self, other):
        if self._get_dtype() is other._get_dtype():
#             other._tlm_sinks.add(self)
#            self._sig = Signal(val=copy.deepcopy(self._dflt), event_set = self.e)
            self._sig = other._subscribe(self)
            self._sig.e = self.e
#             self._sig = other
#             for event in self.e.search(of_type=Event):
#                 getattr(other.e, event).subscribe(event)
            
            self._sourced = True
        else:
            self.inst('_p_dtype_convgen', Process, self._pfunc_dtype_convgen, [], pargs=(other,))

#     def _pfunc_tlm_dispatch(self):
#         while(1):
# #             if self._sig.empty():
# #                 ddic['sim'].wait(self.e['enqueued'])
# #
#             if not self._sig.mem:
#                 ddic['sim'].wait(self.e['enqueued'])
#             
#             for data_recv in self._sig.mem()
#             self._next = self.mem.pop(0)
#             data_recv = self._sig.bpop()
#             for s in self._sinks:
#                 if self._get_dtype() is s._dtype:
#                     s.push(data_recv)
#                 else:
#                     for d, _ in convgen(data_recv, s._dtype):
#                         s.push(d)
#                 
#             while not all([s.empty() for s in self._sinks]):
#                 ddic['sim'].wait(*[s.e['updated'] for s in self._sinks])
                
#             for s in self._sinks:
#                 data_conv_gen = convgen(data_recv, s._get_dtype())
#                  
#                 try:
#                     while True:
#                         s.bpush(next(data_conv_gen))
#                 except StopIteration as e:
#                     if e.value is not None:
#                         s.bpush(e.value)
#                         
#             for s in self._isig_sinks:
#                 data_conv_gen = convgen(data_recv, s._get_dtype())
#                 try:
#                     while True:
#                         s <<= next(data_conv_gen)
#                 except StopIteration as e:
#                     if e.value is not None:
#                         s <<= e.value
    
    def _create_source_sig(self):
        self._sig = Signal(val=copy.deepcopy(self._dflt), event_set = self.e)
#         if self._sinks:
#             self.inst(Process, '_pfunc_tlm_dispatch', self._pfunc_tlm_dispatch)
#         Process('_pfunc_tlm_dispatch', self, self._pfunc_tlm_dispatch)
    
    def bpush(self, val):
#         val = self._prep_write(val)
        
        while not all([s.empty() for s in self._sinks]):
            ddic['sim'].wait(*[s.e['updated'] for s in self._sinks])
        
#         self._sig.bpush(val)
        self.push(val)
        
    def push(self, val):
        val = self._prep_write(val)

        for s in self._sinks:
            s.push(val)
            
#         self._sig.push(val)
        
    def bpop(self):
        if not self._sourced:
            ddic['sim'].wait(self.e['enqueued'])
        
        #print('BPOP: {}, sigid={}, eid={}'.format(self.name, id(self._sig), id(self._sig.e)))
        return self._sig.bpop()
    
    def empty(self):
        if not self._sourced:
            return True
        else:
            return self._sig.empty()
    
    def get_queue(self):
        if not self._sourced:
            return []
        else:
            return self._sig.get_queue()        

