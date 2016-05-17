from sydpy._event import Event
from inspect import signature
import types
from sydpy.component import Component#, compinit, sydsys
from sydpy.wrappers import ObjectProxy

class Intf(Component):

    def __init__(self, name):
        Component.__init__(self, name)
        self._sliced_intfs = {}

    @property
    def val(self):
        return self.read()

    def _connect(self, other, keys=[]):
#         if self._intf_eq(other):
#             self._add_source(other)
        if hasattr(self, '_from_' + other._intf_type):
            getattr(self, '_from_' + other._intf_type)(other, keys)
        elif hasattr(other, '_to_' + self._intf_type):
            getattr(other, '_to_' + self._intf_type)(self, keys)
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

    def _get_dtype(self):
        return self._dtype

    def subscribe(self, proc, event=None):
        if event is None:
            return self.e['event_def'].subscribe(proc)
        else:
            return self.e[event].subscribe(proc)

    def unsubscribe(self, proc, event=None):
        if event is None:
            return self.e['event_def'].unsubscribe(proc)
        else:
            return self.e[event].subscribe(proc)

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
        
class Proxy(object):
    __slots__ = ["_obj", "__weakref__"]
    def __init__(self, obj):
        object.__setattr__(self, "_obj", obj)
    
    #
    # proxying (special cases)
    #
    def __getattribute__(self, name):
        return getattr(object.__getattribute__(self, "_obj"), name)
    def __delattr__(self, name):
        delattr(object.__getattribute__(self, "_obj"), name)
    def __setattr__(self, name, value):
        setattr(object.__getattribute__(self, "_obj"), name, value)
    
    def __nonzero__(self):
        return bool(object.__getattribute__(self, "_obj"))
    def __str__(self):
        return str(object.__getattribute__(self, "_obj"))
    def __repr__(self):
        return repr(object.__getattribute__(self, "_obj"))
    
    #
    # factories
    #
    _special_names = [
        '__abs__', '__add__', '__and__', '__call__', '__cmp__', '__coerce__', 
        '__contains__', '__delitem__', '__delslice__', '__div__', '__divmod__', 
        '__eq__', '__float__', '__floordiv__', '__ge__', '__getitem__', 
        '__getslice__', '__gt__', '__hash__', '__hex__', '__iadd__', '__iand__',
        '__idiv__', '__idivmod__', '__ifloordiv__', '__ilshift__', '__imod__', 
        '__imul__', '__int__', '__invert__', '__ior__', '__ipow__', '__irshift__', 
        '__isub__', '__iter__', '__itruediv__', '__ixor__', '__le__', '__len__', 
        '__long__', '__lshift__', '__lt__', '__mod__', '__mul__', '__ne__', 
        '__neg__', '__oct__', '__or__', '__pos__', '__pow__', '__radd__', 
        '__rand__', '__rdiv__', '__rdivmod__', '__reduce__', '__reduce_ex__', 
        '__repr__', '__reversed__', '__rfloorfiv__', '__rlshift__', '__rmod__', 
        '__rmul__', '__ror__', '__rpow__', '__rrshift__', '__rshift__', '__rsub__', 
        '__rtruediv__', '__rxor__', '__setitem__', '__setslice__', '__sub__', 
        '__truediv__', '__xor__', 'next',
    ]
    
    @classmethod
    def _create_class_proxy(cls, theclass):
        """creates a proxy for the given class"""
        
        def make_method(name):
            def method(self, *args, **kw):
                return getattr(object.__getattribute__(self, "_obj"), name)(*args, **kw)
            return method
        
#         def override_method(name):
#             def method(self, *args, **kw):
#                 return getattr(self, name)(*args, **kw)
#             return method
        
        namespace = {}
        for name in cls._special_names:
            if hasattr(theclass, name):
                namespace[name] = make_method(name)
                
        return type("%s(%s)" % (cls.__name__, theclass.__name__), (cls,), namespace)
    
    def __new__(cls, obj, *args, **kwargs):
        """
        creates an proxy instance referencing `obj`. (obj, *args, **kwargs) are
        passed to this class' __init__, so deriving classes can define an 
        __init__ method of their own.
        note: _class_proxy_cache is unique per deriving class (each deriving
        class must hold its own cache)
        """
        try:
            cache = cls.__dict__["_class_proxy_cache"]
        except KeyError:
            cls._class_proxy_cache = cache = {}
        try:
            theclass = cache[obj.__class__]
        except KeyError:
            cache[obj.__class__] = theclass = cls._create_class_proxy(obj.__class__)
        ins = object.__new__(theclass)
        theclass.__init__(ins, obj, *args, **kwargs)
        return ins

class SlicedIntf(Proxy):
    """Provides access to the parent interface via a key."""
    def __init__(self, intf, key):
        """"Create SlicedIntf of a parent with specific key."""
        #_IntfBase.__init__(self)
        super().__init__(intf)
        self._parent = intf
        self._sliced_dtype = intf._get_dtype().deref(key)
        self._key = key

    def _get_dtype(self):
        return self._sliced_dtype

    def __getattr__(self, name):
        if name in self._parent.c:
            return self._parent.c[name][self._key]
        else:
            return super().__getattr__(name)
#             return getattr(self._parent, name)
#         try:
#             return _IntfBase.__getattr__(self, name)
#         except AttributeError:
#             member = getattr(self._parent, name)
#             
#             if isinstance(member, types.MethodType) and ('keys' in signature(member).parameters):
#                 keys = self._keys
#                 return lambda *args, **kwargs: member(*args, keys=keys, **kwargs)
#             else:
#                 return member
    
    def read(self):
        return self._parent.read()[self._keys]
    
    def write(self, val):
        next_val = self._parent.read_next()
        for k in self._keys[:-1]:
            next_val = next_val[k]
            
        next_val[self._keys[-1]] = val
        return self._parent.write(next_val)
    
    def unsubscribe(self, proc, event=None):
        if event is None:
            self._parent.e.event_def[self._keys].unsubscribe(proc)
        else:
            getattr(self._parent.e, event)[self._keys].unsubscribe(proc)
        
    def subscribe(self, proc, event=None):
        if event is None:
            return self._parent.e.event_def[self._keys].subscribe(proc)
        else:
            getattr(self._parent.e, event)[self._keys].subscribe(proc)
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
