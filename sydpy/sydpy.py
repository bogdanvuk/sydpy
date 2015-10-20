from sydpy.component import Component
from sydpy.configurator import Configurator

class Sydpy(Component):
    
    def __init__(self, conf):
        Component.__init__(self, '/')
        Configurator(self, conf=conf)
