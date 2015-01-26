#  This file is part of sydpy.
# 
#  Copyright (C) 2014-2015 Bogdan Vukobratovic
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

"""Module implements the base classes for the interfaces."""

from sydpy import ConversionError, simwait, Hdlang
from enum import Enum
from sydpy._event import EventSet, Event
import types
from sydpy._util._util import arch
from sydpy._process import always
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
    """Proxy class for one side of an interface."""
    
    def __init__(self, intf, side):
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

    @property    
    def side(self):
        return self._side
    
    @property    
    def intf(self):
        return self._intf

def subintfs(intf, names):
    """List all subinterfaces of an interface in a dictionary."""
    
    if not names:
        names = intf._subintfs
        
    subs = {}
    for name in names:
        subs[name] = getattr(intf, name)
    
    return subs

class _IntfBase(object):
    """Base class for all interfaces and sliced interfaces."""
    
    def __init__(self):
        self.slave = IntfSide(self, IntfDir.slave)
        self.master = IntfSide(self, IntfDir.master)
    
    def __getattr__(self, name):
        return getattr(self.read(), name)
    
    def __ilshift__(self, other):
        self.s_con(other)
        return self
    
    def __irshift__(self, other):
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
    """Base class for all non-sliced interfaces."""
    
    _subintfs = ()
    _intf_type_name = '_Intf'
    _child_side_dict = None
    _slave_channel = None
    _sliced_intfs = None
    _master_channel = None
    __module = None
    _parent = None
    __state = ChIntfState.free
    _src = None
    _drv = None
    _proxies = None
    _init = None
    direction = None
    _cur_val = None
    slave = None
    master = None

    def __init__(self, parent=None, name=None, module=None):
        
        _IntfBase.__init__(self)
        
        self._proxies = []
        self._src = []
        self._parent = parent
        self.name = name
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
    
    def set_channel(self, chnl, side=IntfDir.master):
        if self.get_channel(side) is None:
            if isinstance(chnl, str):
                chnl = self.get_module().get_channel(chnl, side)
            
            if side == IntfDir.master:
                self._master_channel = chnl
            else:
                self._slave_channel = chnl
            
            side_proxy = IntfSide(self, side)
            
            chnl.register_proxy(side_proxy)
    
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

    def _from_generic(self, val):
        return generic_arch, {}
    
    def conv_path(self, other):
        try:
            return getattr(self, '_from_' + other._intf_type())(other)
        except AttributeError:
            pass
        
        try:
            return getattr(other, '_to_' + self._intf_type())(self)
        except AttributeError as e:
            print(e)
        
        return self._from_generic(other)
    
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
            return self._channel.name
    
CsigIntf = namedtuple('CsigIntf', ['elem', 'parent', 'key'])

class csig(_Intf):
    _intf_type_name = 'csig'
    
    def __init__(self, elem, oper, *args, **kwargs):
        _Intf.__init__(self, parent=None, name=None)
        
        self.args = [elem] + list(args)
        self.kwargs = kwargs
        self.oper = oper
        self.senslist = set()

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
    
    def __init__(self, *args, parent=None, name=None, init=None, module=None, **kwargs):
        _Intf.__init__(self, parent=parent, name=name, init=init, module=module)
        self._args = args
        self._kwargs = kwargs
        
        for k in kwargs:
            setattr(self, k, kwargs[k])
        
    def __getitem__(self, key):
        if isinstance(key, int):
            return self._args[key]
        elif isinstance(key, str):
            return self._kwargs[key]
