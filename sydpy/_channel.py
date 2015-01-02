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
from sydpy._util._symexp import SymNodeVisitor
from sydpy._ch_proxy import ChIntfState

"""Module that implements the Channel class."""

from sydpy._component import Component
from sydpy._process import always
from sydpy._util._util import unif_enum
from sydpy._module import Module
from sydpy._util._util import architecture
from sydpy._simulator import simwait
import types

def apply_value(val, asp, keys, old_val):
    if keys is not None:
        try:
            old_val = old_val._replace(keys, val)
        except AttributeError:
            old_val = asp()
            old_val = old_val._replace(keys, val)
            
        val = old_val
                
    return val

def deref_val(val, asp, keys):
    if not keys:
        return asp(val)
    else:
        try:
            return asp(val[keys])
        except TypeError:
            return asp(val)

# def conv_proxy_assignment(val, proxy):
#     
#     try:
#         val = val.read()
#     except AttributeError:
#         pass
#     
#     if isinstance(val, ChannelProxy):
#         val = val.read()
#     elif isinstance(val, tuple):
#         val_list = []
#         for v in val:
#             if isinstance(v, ChannelProxy):
#                 val_list.append(v.read())
#             else:
#                 val_list.append(v)
#             
#         val = con(*val_list)
#     
#     return proxy.aspect(val)

def proxy_keys_connected(p1, p2):
    if isinstance( p1.keys, slice ) :
        high1 = max(p1.keys.start, p1.keys.stop)
        low1 = min(p1.keys.start, p1.keys.stop)
    elif isinstance( p1.keys, int ) :
        high1 = low1 = int(p1.keys)
    else:
        return True
    
    if isinstance( p2.keys, slice ) :
        high2 = max(p2.keys.start, p2.keys.stop)
        low2 = min(p2.keys.start, p2.keys.stop)
    elif isinstance( p2.keys, int ) :
        high2 = low2 = int(p2.keys)
    else:
        return True
    
    if (high1 >= low2) and (high2 >= low1):
        return True
    else:
        return False

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


class AssignVisitor(SymNodeVisitor):
    def __init__(self):
        self.senslist = []
        
    def visit_leaf(self, leaf):
        if hasattr(leaf, 'subscribe'):
            self.senslist.append(leaf)

@architecture
def assign_arch(self, data_i, data_o):
    
    if hasattr(data_i, 'subscribe'):
        sens_list = [data_i]
    else:
        visit = AssignVisitor()
        visit.visit(data_i)
        sens_list = visit.senslist
    
    @always(self, *sens_list)
    def proc():
        data_o.next = data_i.eval()

class Channel(Module):
    """Instances of this class allow the information they carry to be read
    and written in various interfaces (by various protocols)"""
    
    def __init__(self, name, parent, trace = True):
        self.proxies = []
        self.traces = []
        self._tracing = trace
        Module.__init__(self, name, parent)
    
    def register_traces(self, traces):
        if self._tracing:
            self.traces.extend(traces)
    
    def register_proxy(self, proxy):
        self.proxies.append(proxy)
        
        
            
        
    def proxy_state_changed(self, proxy, old_state):
        if ((proxy._state == ChIntfState.driven) and (old_state != ChIntfState.drv_con_wait)) or \
            (proxy._state == ChIntfState.drv_con_wait):
            self.connect_proxies_to_source(proxy)
    
    def assign(self, proxy_from, proxy_to):
        arch = types.MethodType(assign_arch, self)
        proxy_to._state = ChIntfState.drv_con_wait
        self.arch_inst(arch, data_i=proxy_from, data_o=proxy_to)
    
    def read(self, proxy, def_val):
        return self._read('read', proxy, def_val=def_val)
    
    def pop(self, proxy, def_val=None):
        return self._read('pop', proxy, def_val=def_val)
    
    def blk_pop(self, proxy, def_val=None):
        if not proxy.sourced:
            self.connect_to_sources(proxy)
            if not proxy.sourced:
                simwait(proxy.e.enqueued)
                
        return self._read('blk_pop', proxy, def_val=def_val)
    
    def _read(self, func, proxy, def_val=None):
        if not proxy.sourced:
            self.connect_to_sources(proxy)
        
        if proxy.drv:
            return getattr(proxy.drv, func)()
        elif proxy.sourced:
            conv_val = None
            for s in proxy.src:
                val = getattr(s, func)()
                dest_keys, src_keys = get_relative_keys(proxy, s)
                
                if src_keys is not None:
                    val = val.__getitem__(src_keys)
                    
                if dest_keys is not None:
                    conv_val = apply_value(val, proxy.intf, dest_keys, conv_val)
                else:
                    conv_val = val
                        
            return conv_val
        else:
            return def_val
    
    def connect_directly_to_sources(self, proxy):
        for p in self.proxies:
            if p._is_driven():
                if id(p) != id(proxy):
                    if proxy._intf_eq(p):
                        proxy.add_source(p)
                        return True
#                     elif proxy.intf is None:
#                         proxy.intf = p.intf
#                         proxy.add_source(p)
#                         return True
                    
        return False
                    
    def connect_source_directly_to_proxies(self, proxy):
        for p in self.proxies:
            if not p._is_sourced():
                if id(p) != id(proxy):
                    if p._intf_eq(proxy):
                        p.add_source(proxy)
    
    def connect_proxies_to_source(self, proxy):
        
        self.connect_source_directly_to_proxies(proxy)
        
        try:
            for p in self.proxies:
                if not p._is_sourced():
                    if id(p) != id(proxy):
                        try:
                            arch, cfg = p.conv_path(proxy)
                            p._state = ChIntfState.drv_con_wait
                            arch = types.MethodType(arch,self)
                            self.arch_inst(arch, data_i=proxy, data_o=p, **cfg)
                                
#                             self.connect_source_directly_to_proxies(proxy)
#                             self.connect_directly_to_sources(p)
                        except:
                            raise
        except:
            raise
                    
    def connect_to_sources(self, proxy):
 
        if self.connect_directly_to_sources(proxy):
            return
        
        for p in self.proxies:
            if p._is_driven():
                if id(p) != id(proxy):
                    try:
                        arch, cfg = proxy.conv_path(p)
                        proxy._state = ChIntfState.drv_con_wait
                        arch = types.MethodType(arch,self)
                        self.arch_inst(arch, data_i=p, data_o=proxy, **cfg)
                            
#                         self.connect_source_directly_to_proxies(p)
#                         self.connect_directly_to_sources(proxy)
                            
                        return 
                    except:
                        self.connect_directly_to_sources(proxy)
                        raise
                
                
