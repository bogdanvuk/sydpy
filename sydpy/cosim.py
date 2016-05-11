from sydpy.component import Component#, sydsys
from sydpy._util._util import class_load
from sydpy.intfs.intf import Intf
from sydpy.process import Process
from ddi.ddi import Dependency

class Cosim(Component):
    
    def __init__(self, name, cosim_intf: Dependency('xsimintf'), fileset = [], module_name=None, **kwargs):
        super().__init__(name)
        self.cosim_intf = cosim_intf
        self.module_name = module_name
        self.fileset = fileset

        if self.module_name is None:
            self.module_name = self.name.rsplit('/', 1)[-1]
        
        self.cosim_intf.register(self)
    
    def resolve(self):
        self.intfs = {c.name: c for c in self.search(of_type=Intf)}
        self.outputs = {}
        self.inputs = {}
        
        for name, intf in self.intfs.items():
            if intf._mch is None:
                self.inputs[name.rsplit('.',1)[-1]] = intf
            else:
                self.outputs[name.rsplit('.',1)[-1]] = intf
        
        self.inst('proc', Process, self.proc, self.inputs.values())
        
    def proc(self):
        self.cosim_intf.updated(self)
        