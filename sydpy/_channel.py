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

"""Module that implements the Channel class."""

from sydpy._component import Component

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
    

def assign_arch(self, data_i, data_o):
    
    if isinstance(data_i, (Event, ChannelProxy)):
        sens_list = [data_i]
    else:
        sens_list = []
        
        for e in unif_enum(data_i):
            if isinstance(e, (Event, ChannelProxy)):
                sens_list.append(e)
    
    @always(self, *sens_list)
    def proc():
        data_o.next = data_i

class Channel(Component):
    """Instances of this class allow the information they carry to be read
    and written in various aspects (by various protocols)"""
    
    def __init__(self, name, parent):
        self.proxies = set()
        Component.__init__(self, name, parent)
    
    def assign(self, proxy_from, proxy_to):
        assign_arch(self.parent, proxy_from, proxy_to)
      
    def read(self, proxy=None, def_val=None):
        if proxy:
            if not proxy.sourced:
                self.connect_to_sources(proxy)
            
            if proxy.drv:
                return proxy.drv.read()
            elif proxy.sourced:
                conv_val = None
                for s in proxy.src:
                    val = s.read()
                    dest_keys, src_keys = get_relative_keys(proxy, s)
                    
                    if src_keys is not None:
                        val = val.__getitem__(src_keys)
                        
                    if dest_keys is not None:
                        conv_val = apply_value(val, proxy.aspect, dest_keys, conv_val)
                    else:
                        conv_val = val
                            
                return conv_val
            else:
                return def_val
        else:
            return self._read(proxy)
    
    def connect_proxies_to_source(self, proxy):
        
        # First try direct links
        for p in self.proxies.copy():
            if not p.sourced:
                if id(p) != id(proxy):
#                     if proxy_keys_connected(proxy, p):
                    if proxy.aspect == p.aspect:
                        p.add_source(proxy)
        
        for p in self.proxies.copy():
            if not p.sourced:
                if id(p) != id(proxy):
                    try:
                        for arch in p.aspect.conv_path(proxy.aspect):
                            arch(self.parent, p.aspect.clk, proxy, p)
                    except:
                        pass
                    
    def connect_to_sources(self, proxy):
 
        for i in self.proxies.copy():
            if i.drv:
                if proxy_keys_connected(proxy, i):
#                     if proxy.aspect == i.aspect:
                    proxy.add_source(i)
                    return 
