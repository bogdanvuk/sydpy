# from sydpy.component import Component
from sydpy.configurator import Configurator

class System(object):
    
#     def __init__(self, conf):
#         Component.__init__(self, '/')
#         Configurator(self, conf=conf)
        
    def set_conf(self, conf):
        self._conf = conf
        
# system = System()
