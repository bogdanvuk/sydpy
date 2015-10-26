from sydpy.component import Component, system
from sydpy._util._util import class_load
from sydpy.intfs.intf import Intf
from sydpy.process import Process

class Cosim(Component):
    
    def __init__(self, cosim_intf, fileset = [], module_name=None, **kwargs):
        Component.__init__(self, **kwargs)
        self.cosim_intf = system[cosim_intf]
        self.module_name = module_name
        self.fileset = fileset

        if self.module_name is None:
            self.module_name = self.name.rsplit('.', 1)[-1]
        
        self.cosim_intf.register(self)
    
    def resolve(self):
        self.intfs = system.findall(self.name + '.*', of_type=Intf)
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
        