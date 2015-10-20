from sydpy.component import Component

class Unit(Component):
    
    def __init__(self, parent, name, **kwargs):
        Component.__init__(self, name)
        self.__dict__.update(kwargs)
        if parent:
            parent += self
            self._reload_cfg_index()
            self._apply_cfg()
        
        self.build()

    def build(self):
        pass
    
    def _reload_cfg_index(self):
        self.find('/cfg').reload_index()
        
    def _apply_cfg(self):
        self.find('/cfg').apply_cfg_filt(self.qualified_name + '*')
        