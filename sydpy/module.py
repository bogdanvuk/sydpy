from sydpy.unit import Unit
from sydpy.process import Process
from sydpy.intfs.intf import Intf

class Module(Unit):
    
    def __init__(self, parent, name, **kwargs):
        Unit.__init__(self, parent, name, **kwargs)
        self.sim = self.find('/sim')
        
#         for attr in dir(self):
#             if not attr.startswith('_'):
#                 func = getattr(self, attr)
#                 if callable(func):
#                     if hasattr(func, "_senslist"):
#                         self.add(Process(self, func, func._senslist))

    def _get_intfs(self):
        return self.findall(of_type=Intf)

def proc(*args):
    """This process decorator instantiates the Process wrapper object for the process."""

    def _proc(f):
        f._senslist = args
        return f
  
    return _proc

    