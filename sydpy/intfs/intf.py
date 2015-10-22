from sydpy._event import Event

class Intf(object):

    def conn_to_intf(self, other):
        if self._intf_eq(other):
            self._add_source(other)
        else:
            arch, cfg = self.conv_path(other)
            
    def _intf_eq(self, other):
        try:
            if self._intf_type != other._intf_type:
                return False
            
#             if not (self._subintfs == other._subintfs):
#                 return False
#             
#             for s in self._subintfs:
#                 try:
#                     if not getattr(self, s).intf_eq(getattr(other, s)):
#                         return False
#                 except AttributeError:
#                     if not getattr(self, s).cls_eq(getattr(other, s)):
#                         return False
#             
            return True
        except AttributeError:
            return False

#             if arch:
#                 arch = types.MethodType(arch,self.get_module())
#                 self.get_module().arch_inst(arch, data_i=other.master, data_o=self.slave, **cfg)

    def subscribe(self, proc, event=None):
        if event is None:
            return self.e.event_def.subscribe(proc)
        else:
            return getattr(self.e, event).subscribe(proc)

    def unsubscribe(self, proc, event=None):
        if event is None:
            return self.e.event_def.unsubscribe(proc)
        else:
            return getattr(self.e, event).subscribe(proc)
