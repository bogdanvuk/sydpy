from greenlet import greenlet
from sydpy.unit import Unit
from sydpy._util._util import getio_vars

class Process(Unit, greenlet):
    """Wrapper class for functions that implement processes in user modules.
    
    Class turns function in the greenlet task.""" 
   
    def __init__(self, parent, func, senslist=None):
        self.func = func
#         self.func_params = kwargs
#         self.arch = self.module.current_arch
#         self.module.proc_reg(self)
        Unit.__init__(self, parent, func.__name__)
        self.sim = self.find('/sim')
#         self.sim.proc_reg(self) 

        self.senslist = senslist
        if not self.senslist:
            (self.senslist, outputs) = getio_vars(func, intfs=self._parent._get_intfs())

        self._exit_func = None 
        
#         # If the module is to be traslated to HDL, translate the process
#         if module.hdl_gen:
#             self.hdl_gen()
        
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

