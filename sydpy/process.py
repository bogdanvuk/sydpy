from greenlet import greenlet
from sydpy.unit import Unit
from sydpy._util._util import getio_vars
from sydpy.component import Component, compinit, RequiredFeature, system
from sydpy.intfs.intf import Intf

class Process(Component, greenlet):
    """Wrapper class for functions that implement processes in user modules.
    
    Class turns function in the greenlet task.""" 

    sim = RequiredFeature('sim')
   
    @compinit
    def __init__(self, func, senslist=None, **kwargs):
        self.func = func

        self.senslist = senslist
        if not self.senslist:
            parent_name = '.'.join(self.name.split('.')[:-1])
            qname_intfs = system.findall(parent_name + '.*', of_type=Intf)
            intfs = {}
            for k,v in qname_intfs.items():
                intfs[k.rsplit('.', 1)[1]] = v
             
            (self.senslist, outputs) = getio_vars(func, intfs=intfs)
            self.senslist -= outputs

        self._exit_func = None 
        self.sim.proc_reg(self)
        greenlet.__init__(self)
    
    def run(self):
        if self.senslist:
            while(1):
                self.sim.wait(self.senslist)
                self.func()
        else:
            self.func()
            self.sim.wait()
            
    def exit_func(self):
        if self._exit_func:
            self._exit_func()

