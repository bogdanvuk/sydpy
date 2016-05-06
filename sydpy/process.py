from greenlet import greenlet
from sydpy.unit import Unit
from sydpy._util._util import getio_vars
from sydpy.component import Component #, sydsys
from sydpy import Dependency
from sydpy.intfs.intf import Intf

class Process(Component, greenlet):
    """Wrapper class for functions that implement processes in user modules.
    
    Class turns function in the greenlet task.""" 

    def __init__(self, name, func, sim : Dependency('sim'), senslist=None, pargs = (), pkwargs = {}, **kwargs):
        Component.__init__(self, name)
        self.func = func

        self.senslist = senslist
        self.pargs = pargs
        self.pkwargs = pkwargs
        self.sim = sim

        if self.senslist is None:
            if func.__self__ is not None:
#                 parent_name = '.'.join(self.name.split('.')[:-1])
#                 qname_intfs = {c.name: c for c in system.search(parent_name + '.*', of_type=Intf)}
                qname_intfs = {c.name: c for c in func.__self__.search(of_type=Intf)}
                intfs = {}
                for k,v in qname_intfs.items():
                    intfs[k.rsplit('/', 1)[1]] = v
                 
                (inputs, outputs) = getio_vars(func, intfs=intfs)
            
                self.senslist = inputs - outputs

        self._exit_func = None 
        self.sim.proc_reg(self)
        greenlet.__init__(self)
    
    def run(self):
        if self.senslist:
            while(1):
                self.sim.wait(*list(self.senslist))
                self.func(*self.pargs, **self.pkwargs)
        else:
            self.func(*self.pargs, **self.pkwargs)
            self.sim.wait()
            
    def exit_func(self):
        if self._exit_func:
            self._exit_func()
            
#         raise greenlet.GreenletExit 

