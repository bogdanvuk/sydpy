from sydpy.component import Component
from sydpy._signal import Signal
from sydpy._event import EventSet

class isig(Component):
    
    def __init__(self, name, dtype, dflt):
        Component.__init__(self, name)
        self.dtype = dtype
        self.dflt = dflt
        self.e = EventSet(missing_event_handle=self.missing_event)
        
    def con_driver(self, intf):
        pass
    
    def gen_driver(self):
        self._driver = Signal(val=self.dtype.conf(self.dflt), event_set = self.e)
        
    def missing_event(self, event_set, event):
        e = self.create_event(event)
        
#         if not self.is_sourced():
#             self._connect_to_sources()
        
        for s in self._src:
            s_event = getattr(s.e, event)
            s_event.subscribe(e)
        
        return e

