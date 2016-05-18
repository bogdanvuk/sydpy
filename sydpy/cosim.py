from sydpy.component import Component#, sydsys
from sydpy._util._util import class_load
from sydpy.intfs.intf import Intf
from sydpy.process import Process
from ddi.ddi import Dependency, diinit
import os

class Cosim(Component):
    
    def __init__(self, name, fileset = [], module_name=None, cosim_intf: Dependency('xsimintf') = None):
        super().__init__(name)
        self.cosim_intf = cosim_intf
        self.module_name = module_name
        self.fileset = [os.path.abspath(f) for f in fileset]

        if self.module_name is None:
            self.module_name = self.name.rsplit('/', 1)[-1]
        
        self.cosim_intf.register(self)
    
    def resolve_intf(self, intf, feedback=False):
        subintfs = [c for c in intf.search(of_type=Intf)]
        if subintfs:
            for s in subintfs:
                if isinstance(intf, Intf):
                    subintf_feedback = s.name.rpartition('/')[-1] in intf.feedback_subintfs
                else:
                    subintf_feedback = False
                    
                self.resolve_intf(s, feedback=(subintf_feedback!=feedback))
        elif intf is not self:
            name = intf.name[len(self.name)+1:].replace('/', '_')
            if (intf._mch is None) and (feedback==False):
                self.inputs[name] = intf
            else:
                self.outputs[name] = intf

    
    def resolve(self):
        self.inputs = {}
        self.outputs = {}
        self.resolve_intf(self)
        self.inst(Process, 'proc', self.proc, senslist=list(self.inputs.values()))
        
    def proc(self):
        self.cosim_intf.updated(self)
        