from greenlet import greenlet
from sydpy.unit import Unit

class Process(Unit, greenlet):
    """Wrapper class for functions that implement processes in user modules.
    
    Class turns function in the greenlet task.""" 
   
    def __init__(self, parent, func):
        self.func = func
#         self.func_params = kwargs
#         self.arch = self.module.current_arch
#         self.module.proc_reg(self)
        Unit.__init__(self, parent, func.__name__)
        self.sim = self.find('/sim')
#         self.sim.proc_reg(self) 
        senslist = []
        
#         for a in args:
#             if hasattr(a, 'subscribe'):
#                 senslist.append(a)
        
        self.senslist = senslist
#         self._exit_func = exit_func
        self._exit_func = None 
        
#         # If the module is to be traslated to HDL, translate the process
#         if module.hdl_gen:
#             self.hdl_gen()
        
        greenlet.__init__(self)
    
    def run(self):
        if self.senslist:
            while(1):
                self.sim(self.senslist)
                self.func(**self.func_params)
        else:
            self.func(**self.func_params)
            self.sim()
            
    def exit_func(self):
        if self._exit_func:
            self._exit_func()

