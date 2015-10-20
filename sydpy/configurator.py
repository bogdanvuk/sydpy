
from sydpy._util._injector import features
from sydpy.component import Component
import fnmatch
from sydpy._util._util import class_load
from sydpy.unit import Unit

class Configurator(Unit):
    """Class for handling configuration dictionaries."""
    
    def __init__(self, root, conf):
#         self.conf = conf
        Unit.__init__(self, root, "cfg", conf=conf)
       
    def build(self):
        for unit in self.units:
            class_load(unit)(self.parent)
    
    def _reload_cfg_index(self):
        self.reload_index()
    
    def reload_index(self):
        self.root_index = self.parent.index()

    def apply_cfg_filt(self, filt):
        for pat in fnmatch.filter(self.conf.keys(), filt):
            name_pat, attr = pat.partition(".")[::2]
            for qname in fnmatch.filter(self.root_index.keys(), name_pat):  
                self.root_index[qname].__setattr__(attr, self.conf[pat])
