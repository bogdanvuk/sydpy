#  This file is part of sydpy.
# 
#  Copyright (C) 2014 Bogdan Vukobratovic
#
#  sydpy is free software: you can redistribute it and/or modify 
#  it under the terms of the GNU Lesser General Public License as 
#  published by the Free Software Foundation, either version 2.1 
#  of the License, or (at your option) any later version.
# 
#  sydpy is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
# 
#  You should have received a copy of the GNU Lesser General 
#  Public License along with sydpy.  If not, see 
#  <http://www.gnu.org/licenses/>.

from sydpy import ConversionError, simwait, Hdlang
from enum import Enum
from sydpy._signal import Signal
from sydpy.extens.tracing import VCDTrace
from sydpy._event import EventSet, Event
import types
from sydpy._util._util import key_repr, arch
from sydpy._process import always
from sydpy._util._symexp import SymNodeVisitor, SymNode
from sydpy._simulator import simarch_inst
from sydpy._delay import Delay
from collections import namedtuple
from inspect import signature

class ChIntfState(Enum):
    free=1
    bounded=2
    driven=3
    sourced=4
    drv_con_wait=5

class IntfChildSide(Enum):
    master = 1
    slave = 2
    same = 3
    flip = 4
    
class IntfDir(Enum):
    master = 1
    slave = 2

    
    def reverse(self):
        if self.value == IntfDir.master.value:
            return IntfDir.slave
        else:
            return IntfDir.master

class Proxy(object):
    __slots__ = ["_obj", "__weakref__"]
    def __init__(self, obj):
        object.__setattr__(self, "_obj", obj)
    
    #
    # proxying (special cases)
    #
#     def __getattribute__(self, name):
#         return getattr(object.__getattribute__(self, "_obj"), name)

    def __getattribute__(self, name):
#         return getattr(object.__getattribute__(self, "_obj"), name)
        try: 
            return object.__getattribute__(self, name)
        except AttributeError:
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

@arch
def generic_arch(self, data_i, data_o):
    
    @always(self, data_i)
    def proc():
        data_o.next = data_i
        
def proxy_bioper(method):
    def wrapper(self, other):
        if simarch_inst():
            return csig(self, method.__name__, other)
        else:
            try:
                other = other.read()
            except AttributeError:
                pass
            
            return method(self, other)
    return wrapper  

def proxy_unoper(method):
    def wrapper(self):
        if simarch_inst():
            return csig(self, method.__name__)
        else:
            return method(self)
    return wrapper  

class IntfSide(object):
    def __init__(self, intf, side,):
        self._side = side
        self._intf = intf
        
    def __str__(self):
        if self._side == IntfDir.master:
            return str(self._intf) + ".master" 
        else:
            return str(self._intf) + ".slave"
        
    __repr__ = __str__
        
    def connect(self, other):
        try:
            other = other._intf
        except AttributeError:
            pass
        
        self._intf.connect(other, side=self._side)
        
#     def connect(self, other):
#         try:
#             other = other._intf
#         except AttributeError:
#             pass
#         
#         if self._side == IntfDir.slave:
#             self._intf.connect(other)
#         else:
#             other.connect(self)
    
    def conn_to_intf(self, other):
        try:
            other = other._intf
        except AttributeError:
            pass
        
        if self._side == IntfDir.slave:
            self._intf.conn_to_intf(other)
        else:
            other.conn_to_intf(self)
        
    def set_module(self, module):
        self._intf.set_module(module)
        
    def is_sourced(self):
        return self._intf.is_sourced()
#     
#     def __getattr__(self, val):
#         return getattr(self._intf, val)
    
    @property    
    def side(self):
        return self._side
    
    @property    
    def intf(self):
        return self._intf

def subintfs(intf, names):
    if not names:
        names = intf._subintfs
        
    subs = {}
    for name in names:
        subs[name] = getattr(intf, name)
    
    return subs

class _IntfBase(object):
    
    def __init__(self):
        self.slave = IntfSide(self, IntfDir.slave)
        self.master = IntfSide(self, IntfDir.master)
    
    def __getattr__(self, name):
        return getattr(self.read(), name)
    
    def __ilshift__(self, other):
        if self._keys is not None:
            self._parent.s_con(other)
        else:
            self.s_con(other)

        return self
    
    def __irshift__(self, other):
        if self._keys is not None:
            self._parent.assign(other, side=IntfDir.master)
        else:
            self.connect(other, side=IntfDir.master)

        return self

    
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

#     @proxy_bioper
    def __contains__(self, other):
        return self.read() in other

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
    @proxy_unoper
    def __neg__(self):
        return -self.read()
    @proxy_unoper
    def __pos__(self):
        return +self.read()
    @proxy_unoper
    def __abs__(self):
        return abs(self.read())
    @proxy_unoper
    def __invert__(self):
        return ~self.read()
        
    # conversions
    @proxy_unoper
    def __int__(self):
        return int(self.read())
    @proxy_unoper
    def __float__(self):
        return float(self.read())
    @proxy_unoper
    def __oct__(self):
        return oct(self.read())
    @proxy_unoper
    def __hex__(self):
        return hex(self.read())
    @proxy_unoper
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

class SubIntf(_IntfBase):
    
    """Provides access to the parent proxy via a key."""
    def __init__(self, intf, keys=None):
        """"Create SubProxy of a parent with specific key."""
#         self._intf = parent.deref(keys)
        _IntfBase.__init__(self)
        
        self.__dtype = intf._get_dtype().deref(keys)
        self.__keys = keys
        self.__parent = intf

    def _get_dtype(self):
        return self.__dtype

    def __getattr__(self, name):
        member = getattr(self.__parent, name)
        
        if isinstance(member, types.MethodType) and ('keys' in signature(member).parameters):
            keys = self.__keys
            return lambda *args, **kwargs: member(*args, keys=keys, **kwargs)
        else:
            return member

    def connect(self, *args, **kwargs):
        return self.__parent.connect(*args, keys=self.__keys, **kwargs)
    
    def get_channel(self, side=IntfDir.master):
        return None
    
    def read(self):
        return self.__parent.read().__getitem__(self.__keys)
    
    @property
    def next(self):
        raise Exception("Next is write-only property!")
        
    @next.setter
    def next(self, val):
        self.__parent.write(val, keys=self.__keys)

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

    def __ilshift__(self, other):
        self._parent._channel.assign(other, self)
        return None

class _Intf(_IntfBase):
    _subintfs = ()
    _intf_type_name = '_Intf'
    _child_side_dict = None
    _slave_channel = None
    _sliced_intfs = None
    _master_channel = None
    __module = None
    _parent = None
    __state = ChIntfState.free
    _keys = None
    _src = None
    _drv = None
    _proxies = None
    _init = None
    direction = None
    _cur_val = None
    slave = None
    master = None

    def __init__(self, parent=None, name=None, keys=None, module=None):
        
        _IntfBase.__init__(self)
        
        self._proxies = []
        self._src = []
        self._parent = parent
        self.name = name
        self._keys = keys
        self.set_module(module)
        self._sliced_intfs = {}
        
        self.e = EventSet(missing_event_handle=self.missing_event)
        
        if self._parent is not None:
            self.qualif_intf_name = self._parent.qualif_intf_name
        else:
            self.qualif_intf_name = self._intf_type()
            
        if name is not None:
            self.qualif_intf_name += '.' + name
    
    def _intf_type(self):
        return self._intf_type_name
    
    def _get_dtype(self):
        return None    
    
    def set_module(self, module):
        if self.__module is None:
            self.__module = module
    
    def get_module(self):
        if self.__module is not None:
            return self.__module
        else:
            if self._parent is not None:
                return self._parent.get_module()
            else:
                return None
    
#     @property
#     def _module(self):
#         if self.__module is not None:
#             return self.__module
#         else:
#             if self._parent is not None:
#                 return self._parent._module
#             else:
#                 return None
    
#     @property
#     def _master_channel(self):
#         if self.__master_channel is not None:
#             return self.__master_channel
#         else:
#             if self._parent is not None:
#                 return self._parent.__master_channel
#             else:
#                 return None
#             
#     @property
#     def _slave_channel(self):
#         if self.__slave_channel is not None:
#             return self.__slave_channel
#         else:
#             if self._parent is not None:
#                 return self._parent.__slave_channel
#             else:
#                 return None
    
    def set_parent(self, parent):
        self._parent = parent
    
    def get_base_channel(self):
        if self._parent is not None:
            return self._parent.get_base_channel()
        elif self._master_channel is not None:
            return self._master_channel
        else:
            return self._slave_channel
    
    def get_channel(self, side=IntfDir.master):
        if side == IntfDir.master:
            return self._master_channel
        else:
            return self._slave_channel
    
    def change_child_side(self, child_name, side):
        self._child_side_dict[child_name] = side
    
    def get_child_side(self, child_name, side=IntfDir.master):
        return self._child_side_dict[side][child_name]
#         child_side = self._child_side_dict[child_name]
#         if child_side == IntfChildSide.master:
#             return IntfDir.master
#         elif child_side == IntfChildSide.slave:
#             return IntfDir.slave
#         elif child_side == IntfChildSide.same:
#             return side
#         elif child_side == IntfChildSide.flip:
#             return side.reverse()
    
    def assign_subintf(self, proxy, name, other):
        proxy.set_intf(other)
        setattr(self, name, other)
    
#     def assign_intf(self, other, side=IntfDir.slave):
#         if (side == IntfDir.slave):
#             if self.intf_eq(other):
#                 self.add_source(other)
#             else:
#                 arch, cfg = self.conv_path(other)
# #                     self._state = ChIntfState.drv_con_wait
#     #             arch = types.MethodType(arch,self._channel)
#     #             self._channel.arch_inst(arch, data_i=other, data_o=self, **cfg)
#                 arch = types.MethodType(arch,self._module)
#                 self.get_module().arch_inst(arch, data_i=other, data_o=self, **cfg)
#         else:
#             other.assign(self, side.reverse())
    def conn_to_intf(self, other):
        if self.intf_eq(other):
            self.add_source(other)
        else:
            arch, cfg = self.conv_path(other)
            if arch:
                arch = types.MethodType(arch,self.get_module())
                self.get_module().arch_inst(arch, data_i=other.master, data_o=self.slave, **cfg)
    
    def s_con(self, other=None, **subs):
        self.connect(other=other, side=IntfDir.slave, **subs)
        
    def m_con(self, other=None, **subs):
        self.connect(other=other, side=IntfDir.master, **subs)
                
    def connect(self, other=None, side=IntfDir.slave, **subs):
        if other is not None:
            if isinstance(other, str):
                self.set_channel(other, side)
            elif side == IntfDir.master:
                other.connect(self, side=IntfDir.slave)
            elif self.intf_eq(other):
                m_chnl = other.get_channel(side=IntfDir.master)
                s_chnl = other.get_channel(side=IntfDir.slave)
                if m_chnl is not None:
                    self.set_channel(m_chnl, side=IntfDir.slave)
                elif s_chnl is not None:
                    self.set_channel(s_chnl, side=IntfDir.slave)
                else:
                    self.add_source(other)
            else:
                self.conn_to_intf(other)
        else:
            for name, intf in subs.items():
                getattr(self, name).connect(intf, side=self.get_child_side(name, side))
    
#     def assign(self, other, side=IntfDir.slave):
#         if isinstance(other, tuple):
#             if other[0] is not None:
#                 self.assign(other[0], side)
# 
#             for c in other[1]:
#                 try:
#                     getattr(self, c).assign(other[1][c], side=self.get_child_side(c, side).reverse())
#                 except AttributeError:
#                     pass
#         elif isinstance(other, str):
#             self.set_channel(other, side)
#         elif other.get_channel(side.reverse()) is not None:
#             self.set_channel(other.get_channel(side.reverse()), side)
#         else:
#             if side == IntfDir.slave:
#                 self.connect(other)
#             else:
#                 if other.is_driven():
#                     if self._parent is not None:
#                         self._parent.change_child_side(self.name, IntfChildSide.master)
#                         self.connect(other)
#                     else:
#                         raise Exception
#                 else:
#                     other.connect(self)
    
    def set_channel(self, chnl, side=IntfDir.master):
        if self.get_channel(side) is None:
            if isinstance(chnl, str):
                chnl = self.get_module().get_channel(chnl, side)

#             if (side == IntfDir.master) and (chnl.is_driven()):
#                 if self._parent is not None:
#                     self._parent.change_child_side(self.name, IntfChildSide.master)
#                     side = IntfDir.slave
#                 else:
#                     raise Exception
            
            if side == IntfDir.master:
                self._master_channel = chnl
            else:
                self._slave_channel = chnl
            
            side_proxy = IntfSide(self, side)
            
    #         chnl.connect_to_sources(side_proxy)
            chnl.register_proxy(side_proxy)
        
#         self._state = ChIntfState.bounded
        
        
#     @_channel.setter
#     def _channel(self, val, side=):
#         if isinstance(val, tuple):
#             self.__channel = val[0]
# 
#             for c in val[1]:
#                 try:
#                     getattr(self, c)._channel = val[1][c]
#                 except AttributeError:
#                     pass
#         else:
#             self.__channel = val    
#         
#         self._state = ChIntfState.bounded    
#         self.__channel.connect_to_sources(self)
#         self.__channel.register_proxy(self)
    
    @property
    def _state(self):
        return self.__state
    
    @_state.setter
    def _state(self, val):
        if val != self.__state:
            old_state = self.__state
            
            self.__state = val
            if ('_state_' + val.name) in dir(self):
                getattr(self, '_state_' + val.name)()
            
            if self._parent is not None:
                if hasattr(self._parent, '_child_state_changed'):
                    self._parent._child_state_changed(self)
            else:
                if self._master_channel is not None:
                    self._master_channel.proxy_state_changed(self, old_state)
                
                if self._slave_channel is not None:
                    self._slave_channel.proxy_state_changed(self, old_state)
    
#     def set_proxy(self, proxy):
# #         if self.is_bounded():
# #             if proxy._channel is not None:
# #                 if (self._channel != proxy._channel):
# #                     raise Exception
# #         else:
# #         if proxy._channel is not None:
# #             if self._channel != proxy._channel:
# #                 self._channel = proxy._channel
# #             
# #         
# #         self.__module = proxy._parent_module
#         
#         self.e.update(proxy.e)
#         
#         if proxy._init is not None:
#             self.init(proxy._init)
#             
#         self._proxies.append(proxy)
    
    def create_event(self, event):
        if event not in self.e.events:
            e = Event(self, event)
            self.e.add({event:e})
        else:
            e = self.e.events[event]
        
        return e
        
    def missing_event(self, event_set, event):
        e = self.create_event(event)
        
#         if not self.is_sourced():
#             self._connect_to_sources()
        
        for s in self._src:
            s_event = getattr(s.e, event)
            s_event.subscribe(e)
        
        return e
     
    
    def add_source(self, src):
#         if not self._src:
#             self._state = ChIntfState.sourced
            
        self._src = [src]
        
        for e_name in self.e:
            event = getattr(src.e, e_name)
            event.subscribe(self.e[e_name])
        
        if 'connected' in self.e:
            self.e.connected.trigger()
    
    def subscribe(self, proc, event=None):
        if event is None:
            return self.e.event_def.subscribe(proc)
        else:
            return getattr(self.e, event).subscribe(proc)
        
    def unsubscribe(self, proc, event=None):
        if event is None:
            self.e.event_def.unsubscribe(proc)
        else:
            getattr(self.e, event).unsubscribe(proc)
    
    def is_bounded(self):
        return self._channel is not None
    
    def is_sourced(self):
        return bool(self._src)
#         return self.__state in (ChIntfState.driven, ChIntfState.drv_con_wait, ChIntfState.sourced)
       
    def is_driven(self):
        return self._drv is not None
#         return self.__state in (ChIntfState.driven, ChIntfState.drv_con_wait)
    
#     def set_proxy(self, proxy):
#         self._proxy = proxy
#         
#         if self._parent is not None:
#             if hasattr(self._parent, '_child_proxy_con'):
#                 self._parent._child_proxy_con(self)
                       
    @property
    def qualified_name(self):
        return self._get_qualified_name()
    
    def _get_qualified_name(self):
        chnl = self.get_base_channel()
        if chnl is not None:
            return chnl.name + '.' + self.qualif_intf_name
        else:
            return self.qualif_intf_name
        
    def __str__(self):
        return self.qualified_name
    
    __repr__ = __str__
                 
    def copy(self):
        return _Intf(self._parent, self.name, self._proxy)

    def _child_state_changed(self, child=None):
        if self._parent:
            self._parent._child_state_changed(self)

    def _state_driven(self):
        if 'connected' in self.e:
            self.e.connected.trigger()
            
    def _state_sourced(self):
        if 'connected' in self.e:
            self.e.connected.trigger()

    def _intf_parents_eq(self, val):
        parent = self._parent
        val_parent = val._parent
        
        try:
            while (parent is not None) or (val_parent is not None):
                if parent != val_parent:
                    return False
            
                parent = parent._parent
                val_parent = val_parent._parent
            
        except AttributeError:
            return False
        
        return True
    
    def _from_generic(self, val):
        return generic_arch, {}
    
    def conv_path(self, other):
        
#         if self._intf_parents_eq(val) and (self.name == val.name):
        try:
            return getattr(self, '_from_' + other._intf_type())(other)
        except AttributeError:
            pass
        
        try:
            return getattr(other, '_to_' + self._intf_type())(self)
        except AttributeError as e:
            print(e)
        
        return self._from_generic(other)
        
#         raise ConversionError
    
    def intf_eq(self, other):
        try:
            if self._intf_type() != other._intf_type():
                return False
            
            if not (self._subintfs == other._subintfs):
                return False
            
            for s in self._subintfs:
                try:
                    if not getattr(self, s).intf_eq(getattr(other, s)):
                        return False
                except AttributeError:
                    if not getattr(self, s).cls_eq(getattr(other, s)):
                        return False
            
            return True
        except AttributeError:
            return False
    
    def __hash__(self):
        return type.__hash__(self)
    
    def __getitem__(self, key):
        if repr(key) not in self._sliced_intfs:
            sliced_intf = self.deref(key)
            self._sliced_intfs[repr(key)] = sliced_intf
        else:
            sliced_intf = self._sliced_intfs[repr(key)]
        return sliced_intf
      
#     def __getattr__(self, name):
#         if name in self.subintfs:
#             return self.subintfs[name]
#         else:
#             raise AttributeError
    
    def _conv_gen_none(self, other, remain):
        yield other
        return remain
    
#         try:
#             return self._get_dtype().convgen(other, remain)
#         except AttributeError:
#             return self._conv_gen_none(other, remain)
   
    def conv(self, other):
        try:
            return getattr(self, '_from_' + other._intf_type())(other)
        except AttributeError:
            try:
                return getattr(other, '_to_' + self._intf_type())(self)
            except AttributeError:
                raise ConversionError
            
    def _conv_iter(self, other):
        try:
            yield from getattr(self._get_dtype(), '_iter_from_' + other._intf_type())(other)
        except AttributeError:
            try:
                yield from getattr(other, '_iter_to_' + self._get_dtype().__name__)(self.def_subintf)
            except AttributeError:
                raise ConversionError
            
    def __call__(self, *args):
        if args:
            try:
                return self._get_dtype()(args[0])
            except TypeError:
                return args[0]
        else:
            try:
                return self._get_dtype()()
            except TypeError:
                return None
            
    def _connect_to_sources(self):
        if self.__channel is not None:
            self._channel.connect_to_sources(self)
        elif self._parent is not None:
            self._parent._connect_to_sources()
   
    @property
    def next(self):
        raise Exception("Next is write-only property!")
        
    @next.setter
    def next(self, val):
        self.write(val)
        
    @property
    def blk_next(self):
        raise Exception("Next is write-only property!")
        
    @blk_next.setter
    def blk_next(self, val):
        self.blk_write(val)
        
    @property
    def next_after(self):
        raise Exception("Next is write-only property!")
        
    @next_after.setter
    def next_after(self, val):
        simwait(Delay(val[1]))
        self.write(val[0])
   
    def blk_pop(self, def_val=None, keys=None):
        return self._read('blk_pop', def_val, keys)
    
    def read(self, def_val=None, keys=None):
        return self._read('read', def_val, keys)
        
    def _hdl_gen_decl(self, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            return 'logic {0} {1};'.format(self._intf._hdl_gen_decl(), self._channel.name)
            
    def _hdl_gen_ref(self, conv, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            return self._channel.name + key_repr(self._keys)
    
    
class CsigVisitor(object):
    
    def visit_node(self, node):
        self.visit(node.elem)
        for a in node.args:
            self.visit(a)
            
    def visit_leaf(self, leaf):
        pass
    
    def visit(self, node):
        if isinstance(node, SymNode):
            self.visit_node(node)
        else:
            self.visit_leaf(node)

CsigIntf = namedtuple('CsigIntf', ['elem', 'parent', 'key'])

class csig(_Intf):
    _intf_type_name = 'csig'
    
    def __init__(self, elem, oper, *args, **kwargs):
        _Intf.__init__(self, parent=None, name=None, keys=None)
        
        self.args = [elem] + list(args)
        self.kwargs = kwargs
        self.oper = oper
        self.senslist = set()
#         self.create_intf_list()
        
#         self.add_to_senslist(elem)
        
#         for a in self.args:
#             try:
#                 self.add_to_senslist(a)
#             except AttributeError:
#                 pass
#             
#         for key, val in self.kwargs:
#             try:
#                 self.add_to_senslist(val)
#             except AttributeError:
#                 pass
#             
#         for s in self.senslist:
#             for e_name in self.e:
#                 event = getattr(s.e, e_name)
#                 event.subscribe(self.e[e_name])

    def intfs(self):
        for i, a in enumerate(self.args):
            try:
                yield from a.intfs()
            except AttributeError:
                if isinstance(a, _IntfBase):
                    yield CsigIntf(a, self, i)
            
        for key, elem in self.kwargs.items():
            try:
                yield from elem.intfs()
            except AttributeError:
                if isinstance(elem, _IntfBase):
                    yield CsigIntf(elem, self, key)

#     def create_intf_list(self):
#         self.intfs = []
#         for i, a in enumerate(self.args):
#             try:
#                 self.extend(a.intfs)
#             except AttributeError:
#                 if isinstance(a, _Intf):
#                     self.intfs.append(CsigIntf(a, self, i))
#             
#         for key, elem in self.kwargs.items():
#             try:
#                 self.extend(elem.intfs)
#             except AttributeError:
#                 if isinstance(elem, _Intf):
#                     self.intfs.append(CsigIntf(elem, self, key))
                    
    def _replace(self, elem, key):
        if isinstance(key, int):
            self.args[key] = elem
        elif isinstance(key, str):
            self.kwargs[key] = elem

    def add_to_senslist(self, elem):
        try:
            self.senslist.update(elem.senslist)
        except AttributeError:
            if hasattr(elem, 'subscribe'):
                self.senslist.add(elem)

    def missing_event(self, event_set, event):
        e = _Intf.missing_event(self, event_set, event)
        
        for intf in self.intfs():
            intf.elem.subscribe(e, event)
        
        return e
    
    def _read(self, func, def_val=None, keys=None):
        args = []
        
        for a in self.args[1:]:
            try:
                args.append(getattr(a, func)())
            except AttributeError:
                try:
                    args.append(a.eval())
                except AttributeError:
                    args.append(a)
                
        kwargs = {}
        
        for k,v in self.kwargs.items():
            try:
                kwargs[k] = getattr(v, func)()
            except AttributeError:
                try:
                    kwargs[k] = v.eval()
                except AttributeError:
                    kwargs[k] = v
                
        try:
            elem = getattr(self.args[0], func)()
        except AttributeError:
            try:
                elem = self.args[0].eval()
            except AttributeError:
                elem = self.args[0]
        
        return getattr(elem, self.oper)(*args, **kwargs)

class Intf(_Intf):
    
    def __init__(self, *args, parent=None, name=None, keys=None, init=None, module=None, **kwargs):
        _Intf.__init__(self, parent=parent, name=name, keys=keys, init=init, module=module)
        self._args = args
        self._kwargs = kwargs
        
        for k in kwargs:
            setattr(self, k, kwargs[k])
        
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._args[key]
        elif isinstance(key, str):
            return self._kwargs[key]
        
#     def __getattr__(self, name):
#         try:
#             return self._kwargs[name]
#         except KeyError:
#             raise AttributeError
        
        
        

