from sydpy.component import Component#, sydsys
from sydpy._util._util import class_load
from sydpy.intfs.intf import Intf
from sydpy.process import Process
from ddi.ddi import Dependency, diinit
import os
from sydpy.intfs.isig import Csig, Isig, Istruct
from sydpy.types.struct import struct

class Cosim(Component):
    
    def __init__(self, name, fileset = [], module_name=None, cosim_intf: Dependency('xsimintf') = None):
        super().__init__(name)
        self.cosim_intf = cosim_intf
        self.module_name = module_name
        self.fileset = [os.path.abspath(f) for f in fileset]

        if self.module_name is None:
            self.module_name = self.name.rsplit('/', 1)[-1]
        
        self.cosim_intf.register(self)
    
    def resolve_intf(self, intf, feedback=False, master=False):
        subintfs = [c for c in intf.search(of_type=Intf)]
        if subintfs:
            for s in subintfs:
                if isinstance(intf, Intf):
                    subintf_feedback = s.name.rpartition('/')[-1] in intf.feedback_subintfs
                    master = not (intf._mch is None)
                else:
                    master = not (s._mch is None)
                    subintf_feedback = False
                    
                
                    
                self.resolve_intf(s, feedback=(subintf_feedback!=feedback), master=master)
        elif (intf is not self) and (not isinstance(intf, Csig)):
            base_name = os.path.relpath(intf.name, self.name)
            
            if master != feedback:
                direction = self.outputs
            else:
                direction = self.inputs
                
            itype = intf._get_dtype()
            if issubclass(itype, struct):
                struct_intf = self.inst(Istruct, base_name.replace('/', '_'), fields=list(itype.dtype.items()), dflt=intf._dflt) 
                base_name = os.path.dirname(base_name)
                for n, t in itype.dtype.items():
                    direction[os.path.join(base_name, n).replace('/', '_')] = getattr(struct_intf, n)
                
                if direction == self.inputs:
                    intf >> struct_intf
                else:
                    intf << struct_intf
            else:
                direction[base_name.replace('/', '_')] = intf
                
          

    
    def resolve(self):
        self.inputs = {}
        self.outputs = {}
        self.resolve_intf(self)
        self.inst(Process, 'proc', self.proc, senslist=list(self.inputs.values()))
        
    def proc(self):
        self.cosim_intf.updated(self)
        