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
from sydpy.intfs import sig

"""Module that implements the Channel Proxy and related classes."""

from sydpy import Hdlang, ConversionError
from sydpy._util._util import key_repr
from sydpy._util._symexp import SymNode
from sydpy._signal import Signal
from sydpy._event import Event, EventSet
# from sydpy.intfs import sig, tlm
from sydpy._delay import Delay
from sydpy._simulator import simwait, simarch_inst
from enum import Enum

class ConcatProxy(object):
    """Object represents the concatenation of proxy objects and data values."""
    def __init__(self, *args):
        """Initialize ConcatProxy with list of proxy objects and data values."""
        self.elems = args
    
    def read(self):
        """Read proxies and concatenate the values."""
        res = None
        for v in self.elems:
            try:
                val = v.read()
            except AttributeError:
                val = v
                
            if res is None:
                res = val
            else:
                res = res.concat(val)
            
        return res
    
    def _hdl_gen_ref(self, conv, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            s = conv._hdl_gen_ref(self.elems[0])
    
            if len(self.elems) > 1:
                s += ", "
                for e in self.elems[1:]:
                    s += conv._hdl_gen_ref(e)
                    
                s = '{' + s + '}'
                
            return s
        
    @classmethod
    def _hdl_gen_call(cls, conv=None, node=None):
        s = conv._hdl_gen_node(node.args[0])

        if len(node.args) > 1:
            for e in node.args[1:]:
                s += ", "
                s += conv._hdl_gen_node(e)
                
            s = '{' + s + '}'
            
        return s

    def __iter__(self):
        return iter(self.elems)

# ConcatProxy can be created with short form 'con'
con = ConcatProxy

class SubProxy(object):
    """Provides access to the parent proxy via a key."""
    def __init__(self, parent, keys=None):
        """"Create SubProxy of a parent with specific key."""
        self._intf = parent.intf.deref(keys)
        self._keys = keys
        self._parent = parent

    def read(self):
        return self._parent.read().__getitem__(self._keys)
    
    @property
    def next(self):
        raise Exception("Next is write-only property!")
        
    @next.setter
    def next(self, val):
        self._parent.write(val, keys=self._keys)

    def unsubscribe(self, proc):
        self._parent.e.event_def[self._keys].unsubscribe(proc)

    def subscribe(self, proc):
        se = self._parent.e.event_def
        sued = se.__getitem__(self._keys) 
        return sued.subscribe(proc)

    def _hdl_gen_decl(self, lang=Hdlang.Verilog):
        raise Exception("Subproxy cannot declare a _signal!")
            
    def _hdl_gen_ref(self, conv, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            return self._parent._hdl_gen_ref(lang) + key_repr(self._keys)

    def __ilshift__(self, other):
        self._parent._channel.assign(other, self)
        return None

def _apply_subvalue(val, asp, keys, old_val):
    """Update only part of composite data type's value."""
    if keys is not None:
        try:
            old_val = old_val._replace(keys, val)
        except AttributeError:
            old_val = asp()
            old_val = old_val._replace(keys, val)
            
        val = old_val
                
    return val

def proxy_bioper(method):
    def wrapper(self, other):
        if simarch_inst():
            return SymNode(self, method.__name__, other)
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
            return SymNode(self, method.__name__)
        else:
            return method(self)
    return wrapper 

def slice_or_index(high, low):
    if high == low:
        return high
    else:
        return slice(high, low)
    
def get_relative_keys(p1, p2):
    if isinstance( p1.keys, slice ) :
        high1 = max(p1.keys.start, p1.keys.stop)
        low1 = min(p1.keys.start, p1.keys.stop)
    elif isinstance( p1.keys, int ) :
        high1 = low1 = int(p1.keys)
    else:
        high1 = low1 = None
    
    if isinstance( p2.keys, slice ) :
        high2 = max(p2.keys.start, p2.keys.stop)
        low2 = min(p2.keys.start, p2.keys.stop)
    elif isinstance( p2.keys, int ) :
        high2 = low2 = int(p2.keys)
    else:
        high2 = low2 = None

    if (high1, low1) == (None, None):
        if (high2, low2) == (None, None):
            return None, None
        else:
            return slice_or_index(high2, low2), None
    else:
        if (high2, low2) == (None, None):
            return None, slice_or_index(high1, low1)
        else:
            high = min(high1, high2)
            low = max(low1, low2)
    
            return slice_or_index(high - low1, low - low1), slice_or_index(high - low2, low - low2)

class ChIntfState(Enum):
    free=1
    bounded=2
    driven=3
    sourced=4
    drv_con_wait=5

class ChProxy(object):
#     __slots__ = ['subintfs', 'subproxies', 'keys', 'channel', 'intf', 'parent', 
#                  'drv', 'src', 'e', 'qualified_name', 'channel', 'next']
        
    __state = ChIntfState.free
    __channel = None
    __intf = None
    _subintfs = {}
    _sliced_intfs = {}
    _keys = None
    _init = None
    _src = []
    _parent = None
    _intf = None
    _cur_val = None
    _parent_module = None
    e = None
    
    """Channel proxy provides access to the same Channel information using
    different interfaces (protocols)"""
    def __init__(self, parent=None, channel=None, intf=None, init=None, keys=None, parent_module=None, proxy_copy=False):
#     def __init__(self, parent=None, name='', channel=None, parent_module=None, init=None, keys=None):
        """Create new ChProxy instance
        parent     - Module that created the proxy
        channel    - Channel to which proxy is assigned
        intf       - Interface by which to access the Channel 
        keys       - Keys for accessing the parts of Channel data
        """
        self._cur_val = init
        self._init = init
        self._keys = keys
        self._parent = parent
        self._parent_module = parent_module
                
        if channel is not None:
            self._channel = channel
        
        self.e = EventSet(missing_event_handle=self.missing_event)
        
        self._intf = intf
        
        if self._channel is not None:
            self._state = ChIntfState.bounded
        
#         self.init = init
        
#         self.qualified_name = self._parent.qualified_name + "/" + self._channel.name #+ '_' + self.drv_sig_name
        
        
            
#         if parent is None:
#             self._channel.proxies[repr(self)] = self
#             
#             self._channel.connect_to_sources(self)
    
    def _intf_eq(self, other):
        if self._intf is None:
            return True
        else:
            return self._intf._intf_eq(other._intf)
    
    def conv_path(self, other):
        if self._intf is None:
            raise ConversionError
        else:
            return self._intf.conv_path(other._intf)    
    
    @property
    def qualified_name(self):
        return self._channel.qualified_name #+ '_' + self.drv_sig_name
    
    @property
    def sourced(self):
#         if self._intf.def_subintf is not None:
#             def_proxy_sourced = getattr(self, self._intf.def_subintf).sourced
#         else:
#             def_proxy_sourced = False
        
#         return self._src or (self.drv is not None) or self._sourced #or def_proxy_sourced# or (self._parent_proxy is not None) #or self.is_driver
        return self.__state in (ChIntfState.driven, ChIntfState.drv_con_wait, ChIntfState.sourced)
    
    def add_source(self, src):
        if self._intf is None:
            self._intf = src._intf
        
        if not self._src:
            self._state = ChIntfState.sourced
            
        self._src = [src]
        
        for e_name in self.e:
            event = getattr(src.e, e_name)
            event.subscribe(self.e[e_name])
    
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
                self._channel.proxy_state_changed(self, old_state)
    
    def _is_bounded(self):
        return self._channel is not None
    
    def _is_sourced(self):
#         return self.__state in (ChIntfState.driven, ChIntfState.drv_con_wait, ChIntfState.sourced)
        return 
        
    def _is_driven(self):
        if self._intf is None:
            return False
        else:
            return self._intf.driven
        
    def _get_dtype(self):
        try:
            return self._intf._get_dtype()
        except TypeError:
            return None
    
    @property
    def _intf(self):
        return self.__intf
    
    @_intf.setter
    def _intf(self, val):
        if val is not None:
            self.__intf = val.copy()
            self.__intf.set_proxy(self)
        else:
            self.__intf = None
    
    @property
    def _channel(self):
        if self._parent is not None:
            return self._parent._channel
        else:
            return self.__channel
    
    @_channel.setter
    def _channel(self, val):
        self.__channel = val
        self._state = ChIntfState.bounded
        self.__channel.register_proxy(self)
    
    def _convgen(self, val, remain):
        return self._intf._convgen(val, remain)
    
    @property
    def parent_module(self):
        if self._parent is not None:
            return self._parent.parent_module
        else:
            return self._parent_module
    
    @parent_module.setter
    def parent_module(self, val):
        self._parent_module = val
        
#         if self._parent is None:
#             self._channel.proxies[repr(self)] = self
#                 
#             self._channel.connect_to_sources(self)
    
    def _fullname(self):
        name = ''
        if self._parent is not None:
            name = self._parent._fullname() + '_'
        
        if self.__channel is not None:
            name += self.__channel.name + '_'
            
        name += self.name
        
        return name

    def __repr__(self):
        key_str = key_repr(self._keys)
            
        if self._parent_module:
            par_str =  ' from ' + self._parent_module.qualified_name
        else:
            par_str = ''

        return 'to ' + self._channel.qualified_name + par_str + ' with ' + str(self._intf) + key_str + ' intf'

    def __iter__(self):
        val = self.read()
        for v in val:
            yield v
    
    def _apply_subvalue(self, val, keys, old_val):
        """Update only part of composite data type's value."""
        if keys is not None:
            try:
                old_val = old_val._replace(keys, val)
            except AttributeError:
                old_val = self.conv(None)
                old_val = old_val._replace(keys, val)
                
            val = old_val
                    
        return val
    
#     def _state_sourced(self, child=None):
#         if self._parent is None:
#             self._channel.connect_proxies_to_source(self)
#         else:
#             self._parent._state_sourced(self)
#             
#     _state_driven = _state_sourced
#     _state_drv_con_wait = _state_sourced
            
    def get_fullname(self):
        fullname = str(self._intf).replace('.', '_') # + '_' + self.name.replace('.', '_')

        if self._intf.key is not None:
            fullname += '[' + str(self.apsect.key) + ']'
            
        return fullname
    
    def create_event(self, event):
        if event not in self.e.events:
            e = Event(self, event)
            self.e.add({event:e})
        else:
            e = self.e.events[event]
        
        return e
        
    def missing_event(self, event_set, event):
        e = self.create_event(event)
        
        if not self._is_sourced():
            self._connect_to_sources()
        
        for s in self._src:
            s_event = getattr(s.e, event)
            s_event.subscribe(e)
        
        return e
    
    def _connect_to_sources(self):
        if self._parent is not None:
            self._parent._connect_to_sources()
        else:
            if self._channel is not None:
                self._channel.connect_to_sources(self)
    
    def __getitem__(self, key):
        if repr(key) not in self.sliced_intfs:
            sliced_intf = self.deref(key)
            sliced_intf.parent = self
            self.sliced_intfs[repr(key)] = sliced_intf
        else:
            sliced_intf = self.sliced_intfs[repr(key)]
        return sliced_intf
    
    def __getattr__(self, name):
        if name not in self._subintfs:
            subproxy = ChProxy(self, intf = getattr(self.__intf, name), parent_module=self._parent)
            self._subintfs[name] = subproxy
        else:
            subproxy = self._subintfs[name]
             
        return subproxy
    
#     def __getattr__(self, name):
# #         if name == self._intf.def_subintf:
# #             return self
#         if name not in self.subintfs:
#             subintf = ChProxy(self._parent, self._channel, intf = getattr(self._intf, name), parent_proxy=self)
#             self.subintfs[name] = subintf
#         else:
#             subintf = self.subintfs[name]
#             
#         return subintf
    
    def __setattr__(self, name, val):
        if name in dir(self):
            object.__setattr__(self, name, val)
        else:
            subproxy = getattr(self, name)
            subproxy._channel = val._channel
            subproxy.add_source(val)

    def _register_traces(self, traces):
        self._channel.register_traces(traces)

#     def read(self, def_val=None):
#         if self._keys is not None:
#             return self._parent.read(def_val).__getitem__(self._keys)
#         else:
#             return self._intf.read(def_val)
    
    def _write(self, val, func, keys=None):
        if self._keys is not None:
            getattr(self._parent, func)(val, keys=self._keys)
        else:
            if self.__state == ChIntfState.free:
                raise Exception
            else:    
                if self._intf is None:
                    try:
                        self._intf = val._intf
                    except AttributeError:
                        self._intf = sig(val.__class__)
                        
                getattr(self._intf, func)(val)
                
                if self._is_driven():
                    self._state = ChIntfState.driven
                else:
                    raise Exception
        
    def write(self, val, keys=None):
        self._write(val, 'write', keys=keys)
            
    def blk_write(self, val, keys=None):
        self._write(val, 'blk_write', keys=keys)

    def _src_read(self, func):
        conv_val = self._cur_val
        
        for proxy in self._src:
            val = getattr(proxy, func)()
            
            dest_keys, src_keys = get_relative_keys(self, proxy)
                    
            if src_keys is not None:
                val = val.__getitem__(src_keys)
                
            if dest_keys is not None:
                conv_val = self._apply_value(val, dest_keys, conv_val)
            else:
                conv_val = val
                
        return conv_val
    
    def blk_pop(self, def_val=None):
        if self._keys is not None:
            self._cur_val = self._parent.blk_pop(def_val).__getitem__(self._keys)
        else:
            if self.__state == ChIntfState.free:
                if self._cur_val is not None:
                    return self._cur_val
                else:
                    return def_val
                
            if self._parent is None:
                if self.__state == ChIntfState.bounded:
                    self._connect_to_sources()
                
            if self.__state in (ChIntfState.drv_con_wait, ChIntfState.bounded):
                simwait(self.e.connected)
                
            if self.__state == ChIntfState.driven:
                self._cur_val = self._intf.blk_pop()
            elif self.__state == ChIntfState.sourced:
                self._cur_val = self._src_read('blk_pop')
                    
        return self._cur_val
    
    def read(self, def_val=None):
        if self._keys is not None:
            self._cur_val = self._parent.blk_pop(def_val).__getitem__(self._keys)
        else:
#             if self.__state == ChIntfState.free:
            if not self._is_bounded():
                if self._cur_val is not None:
                    return self._cur_val
                else:
                    return def_val
            
            
            
            if self._parent is None:
                if self.__state == ChIntfState.bounded:
                    self._connect_to_sources()
                
#             if self.__state in (ChIntfState.drv_con_wait, ChIntfState.bounded):
#                 simwait(self.e.connected)
                
            if self.__state == ChIntfState.driven:
                self._cur_val = self._intf.read()
            elif self.__state == ChIntfState.sourced:
                self._cur_val = self._src_read('read')
            else:
                self._cur_val = def_val
                    
        return self._cur_val

    eval = read

    @property
    def drv_sig_name(self):
        if self._parent is not None:
            return str(self._intf).replace('.', '_') + key_repr(self._keys) + '_' + self._parent_proxy.drv_sig_name
        else:
            return str(self._intf).replace('.', '_') + key_repr(self._keys)
        
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
     
    def subscribe(self, proc):
        if self._keys is not None:
            se = self._parent.e.event_def
            sued = se.__getitem__(self._keys) 
            return sued.subscribe(proc)
        else:
            return self.e.event_def.subscribe(proc)
        
    def unsubscribe(self, proc):
        if self._keys is not None:
            self._parent.e.event_def[self._keys].unsubscribe(proc)
        else:
            self.e.event_def.unsubscribe(proc)

    def _hdl_gen_decl(self, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            return 'logic {0} {1};'.format(self._intf._hdl_gen_decl(), self._channel.name)
            
    def _hdl_gen_ref(self, conv, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            return self._channel.name + key_repr(self._keys)
    
    def __hash__(self):
        return object.__hash__(self.__repr__())
    
    def __ilshift__(self, other):
        if self._keys is not None:
            self._parent._channel.assign(other, self)
        else:
            self._channel.assign(other, self)
            
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
  
# class ChProxySubintf(ChProxy):
#     """Channel subinterface proxy provides access parts of the interface used to access
#     channel data"""
#     def __init__(self, parent, channel, intf=None, keys=None, parent_proxy=None):
#         """Create new ChProxy instance
#         parent     - Module that created the proxy
#         channel    - Channel to which proxy is assigned
#         intf       - Interface by which to access the Channel 
#         keys       - Keys for accessing the parts of Channel data
#         """
#         self._intf = intf
#         if intf is None:
#             self._intf = sig()
#         
#         self.subproxies = {}
#         self.subintfs = {}
#         self._keys = keys
#         self._channel = channel
# 
#         
#         
#         self._parent = parent
#         self.drv = None
#         self._src = []
#         
#         if intf.name == intf.parent.def_subintf:
#             self.e = parent_proxy.e
#         else:
#             self.e = EventSet(missing_event_handle=self.missing_event)
# 
#         self.qualified_name = self._parent.qualified_name + "/" + self._channel.name + '_' + self.drv_sig_name        
