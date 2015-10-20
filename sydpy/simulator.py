from sydpy.component import Component
from sydpy.unit import Unit
from sydpy._util._util import class_load

class Simulator(Unit):
    '''Simulator kernel.'''

    def __init__(self, parent):
        Unit.__init__(self, parent, "sim")

    def build(self):
        if hasattr(self, 'top'):
            self.top = class_load(self.top)(self.parent, 'top')
    
    def run(self):
        self.gen_drivers()
            
        pass
    
    def gen_drivers(self):
        for _, comp in self.top.index().items():
            if hasattr(comp, '_gen_drivers'):
                comp._gen_drivers()
    
#     def apply_