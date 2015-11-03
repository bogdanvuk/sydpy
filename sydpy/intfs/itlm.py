from sydpy.intfs.isig import isig
from sydpy.process import Process
import copy
from sydpy._signal import Signal
from sydpy.component import sydsys

class itlm(isig):
    _intf_type = 'itlm'
    
#     def _from_tlm(self, val):
#         return _tlm_to_tlm_arch, {}
        
    def _to_isig(self, other):
        self.inst('_p_tlm_to_sig', Process, self._pfunc_tlm_to_sig, [], pargs=(other,))
    
    def _pfunc_tlm_to_sig(self, other):
        while(1):
            other <<= self.bpop()
    
#     def _from_sig(self, val):
#         pass
    
    def bpop(self):
        if not self._sourced:
            sydsys().sim.wait(self.e.enqueued)
            
        return self._sig.bpop()

    def _prep_write(self, val):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        val = self._dtype.conv(val)
        
        if not self._sourced:
            self._sig = Signal(val=copy.deepcopy(self._dflt), event_set = self.e)
            self._sourced = True
            
        return val
    
    def write(self, val):
        val = self._prep_write(val)
        self._sig.push(val)

    push = write
    
    def bpush(self, val):
        val = self._prep_write(val)
        self._sig.bpush(val)
