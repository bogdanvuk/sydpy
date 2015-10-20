from sydpy.component import Component
from sydpy._signal import Signal
from sydpy._event import EventSet
from sydpy.unit import Unit

class isig(Unit):
    
#     def __init__(self, parent, name, dtype, dflt):
#         Unit.__init__(self, name)
#         self.dtype = dtype
#         self.dflt = dflt

    def build(self):
        self.e = EventSet(missing_event_handle=self.missing_event)
        self._mch = None
        self._sch = None
        
    def con_driver(self, intf):
        pass
    
    def _gen_drivers(self):
        if self._mch:
            self._driver = Signal(val=self.dtype.conv(self.dflt), event_set = self.e)
        
    def missing_event(self, event_set, event):
        e = self.create_event(event)
        
#         if not self.is_sourced():
#             self._connect_to_sources()
        
        for s in self._src:
            s_event = getattr(s.e, event)
            s_event.subscribe(e)
        
        return e

