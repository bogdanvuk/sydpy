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
from sydpy._signal import Signal
from sydpy._event import Event, EventSet
from sydpy.aspects import sig

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
        self.aspect = parent.aspect.deref(keys)
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

class ChProxy(object):
    """Channel proxy provides access to the same Channel information using
    different aspects (protocols)"""
    def __init__(self, parent, channel, aspect=None, keys=None): #, parent_proxy=None):
        """Create new ChProxy instance
        parent     - Module that created the proxy
        channel    - Channel to which proxy is assigned
        aspect     - Aspect by which to access the Channel 
        keys       - Keys for accessing the parts of Channel data
        """
        self.keys = keys
        self.channel = channel
        self.aspect = aspect
        
        if aspect is None:
            self.aspect = sig()
        
        self.parent = parent
        self.drv = None
        self.src = []
        
        self.e = EventSet(missing_event_handle=self.missing_event)
        
        self.subproxies = {}
        self.channel.proxies.add(self)
        self.channel.connect_to_sources(self)
    
    def setup_driver(self):
        sig_name = self.channel.name + '_' + self.drv_sig_name
        
        self.drv = self.parent.inst(Signal, sig_name, val=self.aspect(), event_set = self.e)
        
        self.channel.connect_proxies_to_source(self)
        
        if 'connect' in self.e.events:
            self.e.connect.trigger()

    def write(self, val, keys=None):
        if self.drv is None:
            self.setup_driver()
        
        try:
            val = val.read()
        except AttributeError:
            pass
        
        if keys is None:
            val = self.aspect(val)
        else:
            val = _apply_subvalue(val, self.aspect, keys, self.drv._next)
        
        self.drv.write(val)

    def write_after(self, val, delay):
        if isinstance(val, ChProxy):
            val = val.read()
        
        self.drv.write_after(val, delay)
    
    def acquire(self):
        self.cur_val = self.channel.acquire(proxy=self)
        return self.cur_val
   
    def read(self, def_val=None):
        if self.drv is not None:
            self.cur_val = self.drv.read()
        else:
            self.cur_val = self.channel.read(proxy=self, def_val=def_val)
            
        if self.cur_val is None:
            self.cur_val = self.aspect()
            
        return self.cur_val
    
    def blk_write(self, val, delay=0):
        self.channel.blk_write(val, delay, proxy=self)
    
    def blk_read(self):
        self.cur_val = self.channel.blk_read(proxy=self)
        return self.cur_val

    def __repr__(self):
        key_str = key_repr(self.keys)
            
        if self.parent:
            par_str =  ' from ' + self.parent.qualified_name
        else:
            par_str = ''

        return 'to ' + self.channel.qualified_name + par_str + ' with ' + str(self.aspect) + key_str + ' aspect'

    def __iter__(self):
        val = self.read()
        for v in val:
            yield v
            
    @property
    def sourced(self):
        return self.src or (self.drv is not None) # or (self.parent_proxy is not None) #or self.is_driver

    def add_source(self, src):
        if src not in self.src:
            self.src.append(src)
        
        for e_name in self.e:
            event = getattr(src.e, e_name)
            event.subscribe(self.e[e_name])

    def get_fullname(self):
        fullname = str(self.aspect).replace('.', '_') # + '_' + self.name.replace('.', '_')

        if self.aspect.key is not None:
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
    
    @property
    def drv_sig_name(self):
        return str(self.aspect).replace('.', '_') + key_repr(self.keys)
    
    @property
    def next(self):
        raise Exception("Next is write-only property!")
        
    @next.setter
    def next(self, val):
        self.write(val)
#         self.channel.write(val, proxy=self)

    def subscribe(self, proc):
        self.e.event_def.subscribe(proc)
        
    def unsubscribe(self, proc):
        self.e.event_def.unsubscribe(proc)

    def _hdl_gen_decl(self, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            return 'logic {0} {1};'.format(self.aspect._hdl_gen_decl(), self.channel.name)
            
    def _hdl_gen_ref(self, conv, lang=Hdlang.Verilog):
        if lang == Hdlang.Verilog:
            return self.channel.name + key_repr(self.keys)
    
    # comparisons
    def __eq__(self, other):
        if isinstance(other, ChProxy):
            other = other.read()
            
        if isinstance(other, Signal):
            other = other.read()
             
        return self.read() == other
    
    def __hash__(self):
        return object.__hash__(self.__repr__())
    
    def __ilshift__(self, other):
        self.channel.assign(other, self)
        return None
    
    def __invert__(self):
        return ~self.read()        
