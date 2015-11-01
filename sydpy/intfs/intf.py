from sydpy._event import Event
from inspect import signature
import types
from sydpy.component import Component, compinit

def proxy_bioper(method):
    def wrapper(self, other):
        try:
            other = other.read()
        except AttributeError:
            pass
        
        return method(self, other)
    return wrapper  

class _IntfBase(object):
    """Base class for all interfaces and sliced interfaces."""
    
    def __getattr__(self, name):
        return getattr(self.read(), name)
    
    def __hash__(self):
        return id(self)
    
    @proxy_bioper
    def __ilshift__(self, other):
        self.write(other)
        return self
    
#     def __irshift__(self, other):
#         self.connect(other, side=IntfDir.master)
#         return self
    
    def __nonzero__(self):
        if self.read():
            return 1
        else:
            return 0

    # length
    def __len__(self):
        return len(self.read())

    def __bool__(self):
        return bool(self.read())

        
    # integer-like methods

    def __contains__(self, other):
        return self.read() in other
#     
    @proxy_bioper
    def __add__(self, other):
        return self.read() + other
    @proxy_bioper
    def __radd__(self, other):
        return other + self.read()

    @proxy_bioper    
    def __sub__(self, other):
        return self.read() - other
    @proxy_bioper
    def __rsub__(self, other):
        return other - self.read()

    @proxy_bioper
    def __mul__(self, other):
        return self.read() * other
    @proxy_bioper
    def __rmul__(self, other):
        return other * self.read()

    @proxy_bioper
    def __div__(self, other):
        return self.read() / other
    @proxy_bioper
    def __rdiv__(self, other):
        return other / self.read()

    @proxy_bioper    
    def __truediv__(self, other):
        return self.read().__truediv__(other)
    @proxy_bioper
    def __rtruediv__(self, other):
        return other.__truediv__(self.read())
    
    @proxy_bioper
    def __floordiv__(self, other):
        return self.read() // other
    @proxy_bioper
    def __rfloordiv__(self, other):
        return other //  self.read()

    @proxy_bioper    
    def __mod__(self, other):
        return self.read() % other
    @proxy_bioper
    def __rmod__(self, other):
        return other % self.read()

    # XXX divmod

    @proxy_bioper    
    def __pow__(self, other):
        return self.read() ** other
    def __rpow__(self, other):
        return other ** self.read()

    @proxy_bioper
    def __lshift__(self, other):
        return self.read() << other
    @proxy_bioper
    def __rlshift__(self, other):
        return other << self.read()

    @proxy_bioper            
    def __rshift__(self, other):
        return self.read() >> other
    @proxy_bioper
    def __rrshift__(self, other):
        return other >> self.read()

    @proxy_bioper           
    def __and__(self, other):
        return self.read() & other
    @proxy_bioper
    def __rand__(self, other):
        return other & self.read()

    @proxy_bioper
    def __or__(self, other):
        return self.read() | other
    @proxy_bioper
    def __ror__(self, other):
        return other | self.read()
    
    @proxy_bioper
    def __xor__(self, other):
        return self.read() ^ other
    @proxy_bioper
    def __rxor__(self, other):
        return other ^ self.read()
    
    def __neg__(self):
        return -self.read()
    
    def __pos__(self):
        return +self.read()
    
    def __abs__(self):
        return abs(self.read())
    
    def __invert__(self):
        return ~self.read()
        
    # conversions
    
    def __int__(self):
        return int(self.read())
    
    def __float__(self):
        return float(self.read())
    
    def __oct__(self):
        return oct(self.read())
    
    def __hex__(self):
        return hex(self.read())
    
    def __index__(self):
        return int(self.read())
    # comparisons
    @proxy_bioper
    def __eq__(self, other):
#         try:
#             other = other.read()
#         except AttributeError:
#             pass
        return self.read() == other
    
    @proxy_bioper
    def __ne__(self, other):
        return self.read() != other 
    @proxy_bioper
    def __lt__(self, other):
        return self.read() < other
    @proxy_bioper
    def __le__(self, other):
        return self.read() <= other
    @proxy_bioper
    def __gt__(self, other):
        return self.read() > other
    @proxy_bioper
    def __ge__(self, other):
        return self.read() >= other

class SlicedIntf(_IntfBase):
    """Provides access to the parent interface via a key."""
    def __init__(self, intf, keys=None):
        """"Create SlicedIntf of a parent with specific key."""
        _IntfBase.__init__(self)
        
        self.__dtype = intf._get_dtype().deref(keys)
        self.__keys = keys
        self.__parent = intf

    def _get_dtype(self):
        return self.__dtype

    def __getattr__(self, name):
        try:
            return _IntfBase.__getattr__(self, name)
        except AttributeError:
            member = getattr(self.__parent, name)
            
            if isinstance(member, types.MethodType) and ('keys' in signature(member).parameters):
                keys = self.__keys
                return lambda *args, **kwargs: member(*args, keys=keys, **kwargs)
            else:
                return member
    
    def read(self):
        return self.__parent.read().__getitem__(self.__keys)
    
    def write(self, val):
        next_val = self.__parent.read_next()
        next_val[self.__keys] = val
        return self.__parent.write(next_val)
    
    def unsubscribe(self, proc, event=None):
        if event is None:
            self.__parent.e.event_def[self.__keys].unsubscribe(proc)
        else:
            getattr(self.__parent.e, event)[self.__keys].unsubscribe(proc)
        
    def subscribe(self, proc, event=None):
        if event is None:
            return self.__parent.e.event_def[self.__keys].subscribe(proc)
        else:
            getattr(self.__parent.e, event)[self.__keys].subscribe(proc)
#     def _hdl_gen_decl(self, lang=Hdlang.Verilog):
#         raise Exception("Subproxy cannot declare a _signal!")
#             
#     def _hdl_gen_ref(self, conv, lang=Hdlang.Verilog):
#         if lang == Hdlang.Verilog:
#             return self._parent._hdl_gen_ref(lang) + key_repr(self._keys)
# 
#     def __ilshift__(self, other):
#         self.write(other)
#         return self

class Intf(Component, _IntfBase):

    def __init__(self, **kwargs):
        Component.__init__(self, **kwargs)
        self._sliced_intfs = {}

    def _connect(self, other):
        if self._intf_eq(other):
            self._add_source(other)
        elif hasattr(self, '_from_' + other._intf_type):
            getattr(self, '_from_' + other._intf_type)(other)
        elif hasattr(other, '_to_' + self._intf_type):
            getattr(other, '_to_' + self._intf_type)(self)
        else:
            raise Exception('Cannot connect to master interface!')
            
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

    def __str__(self):
        return str(self.read())

    def __setitem__(self, key, val):
        pass

    def __getitem__(self, key):
        if repr(key) not in self._sliced_intfs:
            sliced_intf = self.deref(key)
            self._sliced_intfs[repr(key)] = sliced_intf
        else:
            sliced_intf = self._sliced_intfs[repr(key)]
        return sliced_intf
        
