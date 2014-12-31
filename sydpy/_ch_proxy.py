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

"""Module that implements the Channel Proxy and related classes."""

from sydpy import Hdlang
from sydpy._util._util import key_repr
from sydpy._util._symexp import SymNode
from sydpy._signal import Signal
from sydpy._event import Event, EventSet
from sydpy.intfs import sig, tlm
from sydpy._delay import Delay
from sydpy._simulator import simwait, simarch_inst

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
        self.intf = parent.intf.deref(keys)
        self.keys = keys
        self.parent = parent

    def read(self):
        return self.parent.read().__getitem__(self.keys)
    
    @property
    def next(self):
        raise Exception("Next is write-only property!")
        
    @next.setter
    def next(self, val):
        self.parent.write(val, keys=self.keys)

    def unsubscribe(self, proc):
        self.parent.e.event_def[self.keys].unsubscribe(proc)

    def subscribe(self, proc):
        se = self.parent.e.event_def
        sued = se.__getitem__(self.keys) 
        return sued.subscribe(proc)

    def _hdl_gen_decl(self, lang=Hdlang.Verilog):
        raise Exception("Subproxy cannot declare a _signal!")
            
    def _hdl_gen_ref(self, conv, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            return self.parent._hdl_gen_ref(lang) + key_repr(self.keys)

    def __ilshift__(self, other):
        self.parent.channel.assign(other, self)
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

class ChProxy(object):
#     __slots__ = ['subintfs', 'subproxies', 'keys', 'channel', 'intf', 'parent', 
#                  'drv', 'src', 'e', 'qualified_name', 'channel', 'next']
    
    """Channel proxy provides access to the same Channel information using
    different interfaces (protocols)"""
    def __init__(self, parent, channel, intf=None, init=None, keys=None, parent_proxy=None, proxy_copy=False):
        """Create new ChProxy instance
        parent     - Module that created the proxy
        channel    - Channel to which proxy is assigned
        intf       - Interface by which to access the Channel 
        keys       - Keys for accessing the parts of Channel data
        """
        self.intf = intf
#         if intf is None:
#             self.intf = sig()
            
        self.subproxies = {}
        self.subintfs = {}
        self.keys = keys
        self.channel = channel
        self.parent = parent
        self.drv = None
        self.src = []
        self.parent_proxy = parent_proxy
        self.init = init
        
        self.qualified_name = self.parent.qualified_name + "/" + self.channel.name + '_' + self.drv_sig_name
        
        self.e = EventSet(missing_event_handle=self.missing_event)
            
        if parent_proxy is None:
            self.channel.proxies[repr(self)] = self
            
            if not proxy_copy:
                self.channel.connect_to_sources(self)
        
    def setup_driver(self):
        sig_name = self.channel.name
        
        if self.drv_sig_name:
            sig_name += '_' + self.drv_sig_name
        
        self.drv = self.parent.inst(Signal, sig_name, val=self.intf(), event_set = self.e)
        
        self.channel.connect_proxies_to_source(self)
        
        if 'connect' in self.e.events:
            self.e.connect.trigger()
            
#         if self.parent_proxy is not None:
#             self.channel.connect_proxies_to_source(self.parent_proxy)

    def _write_prep(self, val, keys=None):
        if self.drv is None:
            self.setup_driver()
        
        try:
            val = val.read()
        except AttributeError:
            pass
        
        if keys is None:
            val = self.intf(val)
        else:
            val = _apply_subvalue(val, self.intf, keys, self.drv._next)
            
        return val
            
    def blk_write(self, val, keys=None):
        val = self._write_prep(val, keys)
        self.drv.blk_push(val)

    def write(self, val, keys=None):
        val = self._write_prep(val, keys)
        
        if isinstance(self.intf, tlm):
            self.drv.push(val)
        else:
            self.drv.write(val)

    def write_after(self, val, delay):
        if isinstance(val, ChProxy):
            val = val.read()
        
        self.drv.write_after(val, delay)
    
    def acquire(self):
        self.cur_val = self.channel.acquire(proxy=self)
        return self.cur_val

    def blk_pop(self):
        if self.drv is not None:
            self.cur_val = self.drv.blk_pop()
        else:
            self.cur_val = self.channel.blk_pop(proxy=self)
            
        if self.cur_val is None:
            if self.init is not None:
                self.cur_val = self.init
            else:
                self.cur_val = self.intf()
            
        return self.cur_val
        
    def pop(self):
        if self.drv is not None:
            self.cur_val = self.drv.pop()
        else:
            self.cur_val = self.channel.pop(proxy=self)
            
        if self.cur_val is None:
            if self.init is not None:
                self.cur_val = self.init
            else:
                self.cur_val = self.intf()
            
        return self.cur_val
   
    def read(self, def_val=None):
        if self.drv is not None:
            self.cur_val = self.drv.read()
        else:
            self.cur_val = self.channel.read(proxy=self, def_val=def_val)
            
        if self.cur_val is None:
            if self.init is not None:
                self.cur_val = self.init
            else:
                self.cur_val = self.intf()
            
        return self.cur_val
    
#     def blk_write(self, val, keys=None):
#         if self.intf.def_subintf is not None:
#             getattr(self, self.intf.def_subintf)._blk_write(val, keys)
#         else:
#             self._blk_write(val, keys)
#     
#     def blk_pop(self):
#         if self.intf.def_subintf is not None:
#             return getattr(self, self.intf.def_subintf)._blk_pop()
#         else:
#             return self._blk_pop()
#             
#     def pop(self):
#         if self.intf.def_subintf is not None:
#             return getattr(self, self.intf.def_subintf)._pop()
#         else:
#             return self._pop()
#             
#     def write(self, val, keys=None):
#         if self.intf.def_subintf is not None:
#             getattr(self, self.intf.def_subintf)._write(val, keys)
#         else:
#             self._write(val, keys)
#     
#     def read(self, def_val=None):
#         if self.intf.def_subintf is not None:
#             return getattr(self, self.intf.def_subintf)._read(def_val)
#         else:
#             return self._read(def_val)
        
    eval = read
    
    def blk_read(self):
        self.cur_val = self.channel.blk_read(proxy=self)
        return self.cur_val

    def __repr__(self):
        key_str = key_repr(self.keys)
            
        if self.parent:
            par_str =  ' from ' + self.parent.qualified_name
        else:
            par_str = ''

        return 'to ' + self.channel.qualified_name + par_str + ' with ' + str(self.intf) + key_str + ' intf'

    def __iter__(self):
        val = self.read()
        for v in val:
            yield v
            
    @property
    def sourced(self):
#         if self.intf.def_subintf is not None:
#             def_proxy_sourced = getattr(self, self.intf.def_subintf).sourced
#         else:
#             def_proxy_sourced = False
        
        return self.src or (self.drv is not None) #or def_proxy_sourced# or (self.parent_proxy is not None) #or self.is_driver

    def add_source(self, src):
        if src not in self.src:
            self.src.append(src)
        
        for e_name in self.e:
            event = getattr(src.e, e_name)
            event.subscribe(self.e[e_name])

    def get_fullname(self):
        fullname = str(self.intf).replace('.', '_') # + '_' + self.name.replace('.', '_')

        if self.intf.key is not None:
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
        
        if not self.sourced:
            self.channel.connect_to_sources(self)
        
        for s in self.src:
            s_event = getattr(s.e, event)
            s_event.subscribe(e)
        
        return e
    
    def __getitem__(self, key):
        if repr(key) not in self.subproxies:
            subproxy = SubProxy(self, keys=key)
            self.subproxies[repr(key)] = subproxy
        else:
            subproxy = self.subproxies[repr(key)]
        return subproxy
    
    def __getattr__(self, name):
        if name == self.intf.def_subintf:
            return self
        elif name not in self.subintfs:
            subintf = ChProxy(self.parent, self.channel, intf = getattr(self.intf, name), parent_proxy=self)
            self.subintfs[name] = subintf
        else:
            subintf = self.subintfs[name]
            
        return subintf
    
    def __setattr__(self, name, val):
        if name == 'intf':
            object.__setattr__(self, 'intf', val)
        elif self.intf is None:
            object.__setattr__(self, name, val)
        elif name in self.intf.subintfs:
            self.subintfs[name] = val 
#         elif name in self.__slots__:
        else:
            object.__setattr__(self, name, val)
#         else:
#             raise AttributeError

    @property
    def drv_sig_name(self):
        return str(self.intf).replace('.', '_') + key_repr(self.keys)
    
    @property
    def next(self):
        raise Exception("Next is write-only property!")
        
    @next.setter
    def next(self, val):
        self.write(val)
        
    @property
    def blk_next(self):
        raise Exception("Next is write-only property!")
        
    @next.setter
    def blk_next(self, val):
        self.blk_write(val)
        
    @property
    def next_after(self):
        raise Exception("Next is write-only property!")
        
    @next.setter
    def next_after(self, val):
        simwait(Delay(val[1]))
        self.write(val[0])
        
    def subscribe(self, proc):
        self.e.event_def.subscribe(proc)
        
    def unsubscribe(self, proc):
        self.e.event_def.unsubscribe(proc)

    def _hdl_gen_decl(self, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            return 'logic {0} {1};'.format(self.intf._hdl_gen_decl(), self.channel.name)
            
    def _hdl_gen_ref(self, conv, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            return self.channel.name + key_repr(self.keys)
    
    def __hash__(self):
        return object.__hash__(self.__repr__())
    
    def __ilshift__(self, other):
        self.channel.assign(other, self)
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
#         self.intf = intf
#         if intf is None:
#             self.intf = sig()
#         
#         self.subproxies = {}
#         self.subintfs = {}
#         self.keys = keys
#         self.channel = channel
# 
#         
#         
#         self.parent = parent
#         self.drv = None
#         self.src = []
#         
#         if intf.name == intf.parent.def_subintf:
#             self.e = parent_proxy.e
#         else:
#             self.e = EventSet(missing_event_handle=self.missing_event)
# 
#         self.qualified_name = self.parent.qualified_name + "/" + self.channel.name + '_' + self.drv_sig_name        
