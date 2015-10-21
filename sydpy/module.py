from sydpy.unit import Unit
from sydpy.process import Process

class Module(Unit):
    
    def __init__(self, parent, name, **kwargs):
        Unit.__init__(self, parent, name, **kwargs)
        self.sim = self.find('/sim')
        
        for attr in dir(self):
            if not attr.startswith('_'):
                func = getattr(self, attr)
                if callable(func):
                    if hasattr(func, "_is_process"):
                        self.add(Process(self, func))
        
def proc(f):
    f._is_process = True
    return f
    