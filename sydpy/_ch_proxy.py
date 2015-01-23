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
from sydpy.intfs import sig, csig


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

class ChProxy(object):
#     __slots__ = ['subintfs', 'subproxies', 'keys', 'channel', 'intf', 'parent', 
#                  'drv', 'src', 'e', 'qualified_name', 'channel', 'next']
        
    __channel = None
    _keys = None
    _init = None
    
    _parent = None
    _intf = None
    _cur_val = None
    _parent_module = None
    e = None
    _subintfs = None
    _sliced_intfs = None
    
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
        self._subintfs = {}
        self._sliced_intfs = {}
    
        self._cur_val = init
        self._init = init
        self._keys = keys
        self._parent = parent
        self._parent_module = parent_module
                
        self._channel = channel
        
        self.e = EventSet(missing_event_handle=self.missing_event)
        
        self.set_intf(intf)
#         self.init = init
        
#         self.qualified_name = self._parent.qualified_name + "/" + self._channel.name #+ '_' + self.drv_sig_name
        
        
            
#         if parent is None:
#             self._channel.proxies[repr(self)] = self
#             
#             self._channel.connect_to_sources(self)
    

    @property
    def _channel(self):
        if self._intf is not None:
            return self._intf._channel
        else:
            return self.__channel
    
    @_channel.setter
    def _channel(self, val):
        if self._intf is not None:
            self._intf._channel = val
        else:
            self.__channel = val

    def init(self, val):
        self._init = val

    def get_intf(self):
        if self._intf is None:
            try:
                self.set_intf(self._channel.request_interface())
            except:
                pass
            
        return self._intf

    
    def set_intf(self, intf):
        
        try:
            intf = intf._intf
        except AttributeError:
            pass
        
        if intf is not None:
            intf.set_proxy(self)
            
            self.e = intf.e
            self.read = intf.read
            self.write = intf.write
            self._get_dtype = intf._get_dtype
            self.blk_pop = intf.blk_pop
            self.blk_write = intf.blk_write
            self.subscribe = intf.subscribe
            self.unsubscribe = intf.unsubscribe
#             from operator import attrgetter
#             self._channel = intf.__class__._channel #property(intf.__class._channel.fget(self), intf._channel.fset(self))
#             self._channel = attrgetter('_intf._channel')
            self.init = intf.init
        
        self._intf = intf
    
    def _has_intf(self):
        return self._intf is not None 
        
    @property
    def qualified_name(self):
        if self._intf is not None:
            return self._intf.qualified_name
        elif self._channel is not None:
            return self._channel.qualified_name #+ '_' + self.drv_sig_name
        else:
            return "Proxy"
    
    def _get_dtype(self):
        return None
    
#     @property
#     def _channel(self):
#         if self._parent is not None:
#             return self._parent._channel
#         else:
#             return self.__channel
#     
#     @_channel.setter
#     def _channel(self, val):
#         self.__channel = val
#         self._state = ChIntfState.bounded
#         self.__channel.register_proxy(self)
#     
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

        if self._channel is not None:
            ch_str = ' to ' + self._channel.qualified_name 
        else:
            ch_str = ''
            
        if self._intf is not None:
            intf_str = ' with ' + str(self._intf) + key_str + ' intf'
        else:
            intf_str = ' no interface'
            
        return par_str + ch_str + intf_str
        

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
        self.get_intf()
        
        e = self.create_event(event)
        return e
    
    def _connect_to_sources(self):
        if self._parent is not None:
            self._parent._connect_to_sources()
        else:
            if self._channel is not None:
                self._channel.connect_to_sources(self)
    
    def __getitem__(self, key):
        if repr(key) not in self._sliced_intfs:
            sliced_intf = ChProxy(self, intf = self._intf.deref(key), parent_module=self._parent_module)
            self._sliced_intfs[repr(key)] = sliced_intf
        else:
            sliced_intf = self._sliced_intfs[repr(key)]
        return sliced_intf
    
    def __getattr__(self, name):
        if name not in self._subintfs:
            subproxy = ChProxy(self, intf = getattr(self._intf, name), parent_module=self._parent_module)
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
#             setattr(self._intf, name, val.get_intf())
            self._intf.assign_subintf(getattr(self, name), name, val.get_intf())
            
# 
#     def _register_traces(self, traces):
#         self._channel.register_traces(traces)

#     def read(self, def_val=None):
#         if self._keys is not None:
#             return self._parent.read(def_val).__getitem__(self._keys)
#         else:
#             return self._intf.read(def_val)
    
    def _write(self, val, func, keys=None):
        if self._keys is not None:
            getattr(self._parent, func)(val, keys=self._keys)
        else:
            if self.get_intf() is not None:
                self.cur_val = getattr(self, func)(val, keys)
            else:

                try:
                    self.set_intf(val.get_intf().copy())
                    return getattr(self, func)(val, keys)
                except:
                    pass
                
                self._cur_val = val
        
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
            if self._intf is not None:
                try:
                    self._intf.assign(other.get_intf())
                except AttributeError:
                    intf = csig()
                    other_proxy = ChProxy(channel=None, parent_module=self, intf=intf, init=other)
                    self._intf.assign(other_proxy.get_intf())
            else:
                raise Exception
            
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
