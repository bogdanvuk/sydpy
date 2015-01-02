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

from sydpy import ConversionError, simwait
from enum import Enum
from sydpy._signal import Signal
from sydpy.extens.tracing import VCDTrace

class Intf(object):
    _subintfs = ()
    proxy = None

    def __init__(self, parent=None, name=None, proxy=None):
        self.parent = parent
        self.name = name
        
        if proxy is not None:
            self.set_proxy(proxy)
        
        if self.parent is not None:
            self.qualif_intf_name = self.parent.qualif_intf_name + '.' + name
        else:
            self.qualif_intf_name = self.__class__.__name__
    
    def set_proxy(self, proxy):
        self.proxy = proxy
        
        if self.parent is not None:
            if hasattr(self.parent, '_child_proxy_con'):
                self.parent._child_proxy_con(self)
                       
    @property
    def qualified_name(self):
        if self.proxy is not None:
            if self.proxy._channel is not None:
                return self.proxy._channel.name + '.' + self.qualif_intf_name
            else:
                return self.qualif_intf_name
        else:
            return self.qualif_intf_name
        
    def __str__(self):
        return self.qualified_name
    
    __repr__ = __str__
                 
    def copy(self):
        return Intf(self.parent, self.name, self.proxy)

    def _child_state_changed(self, child=None):
        if self.parent:
            self.parent._child_state_changed(self)

    def _state_driven(self):
        self.drv.e.connected.trigger()

    def _intf_parents_eq(self, val):
        parent = self.parent
        val_parent = val.parent
        
        try:
            while (parent is not None) or (val_parent is not None):
                if parent != val_parent:
                    return False
            
                parent = parent.parent
                val_parent = val_parent.parent
            
        except AttributeError:
            return False
        
        return True
    
    def _get_dtype(self):
        try:
            return self.def_subintf._get_dtype()
        except AttributeError:
            return self.def_subintf
    
    def conv_path(self, val):
        
        if self._intf_parents_eq(val) and (self.name == val.name):
            try:
                return getattr(self, '_from_' + val.__class__.__name__)(val)
            except AttributeError:
                return getattr(val, '_to_' + self.__class__.__name__)(self)
        
        raise ConversionError
    
    def _intf_eq(self, other):
        try:
            if self.__class__ != other.__class__:
                return False
            
            if not (self._subintfs == other._subintfs):
                return False
            
            for s in self._subintfs:
                try:
                    if not getattr(self, s)._intf_eq(getattr(other, s)):
                        return False
                except AttributeError:
                    if getattr(self, s) != getattr(other, s):
                        return False
            
            return True
        except AttributeError:
            return False
    
    def __hash__(self):
        return type.__hash__(self)
         
#     def __getattr__(self, name):
#         if name in self.subintfs:
#             return self.subintfs[name]
#         else:
#             raise AttributeError
    
    def _conv_gen_none(self, other, remain):
        yield other
        return remain
    
    def _convgen(self, other, remain=None):
        return self.def_subintf._convgen(other, remain)
#         try:
#             return self.dtype.convgen(other, remain)
#         except AttributeError:
#             return self._conv_gen_none(other, remain)
   
    def conv(self, other):
        try:
            return getattr(self, '_from_' + other.__class__.__name__)(other)
        except AttributeError:
            try:
                return getattr(other, '_to_' + self.__class__.__name__)(self)
            except AttributeError:
                return self.def_subintf.conv(other)
            
    def _conv_iter(self, other):
        try:
            yield from getattr(self.dtype, '_iter_from_' + other.__class__.__name__)(other)
        except AttributeError:
            try:
                yield from getattr(other, '_iter_to_' + self.dtype.__name__)(self.def_subintf)
            except AttributeError:
                raise ConversionError
            
    def __call__(self, *args):
        if args:
            try:
                return self.dtype(args[0])
            except TypeError:
                return args[0]
        else:
            try:
                return self.dtype()
            except TypeError:
                return None
            
    def setup_driver(self):
        if self.drv is None:
            self.drv = Signal(val=self.conv(None), event_set = self.proxy.e)
            try:
                self.proxy._register_traces([VCDTrace(self.qualified_name, self)])
            except KeyError:
                pass
                    
    def write(self, val, keys=None):
        self.setup_driver()
        val = self._write_prep(val, keys)
                
        self.drv.write(val)        
        
    def _write_prep(self, val, keys=None):
        if self.drv is None:
            self.setup_driver()
        
        try:
            val = val.read()
        except AttributeError:
            pass
        
        if keys is None:
            val = self.conv(val)
        else:
            val = self._apply_subvalue(val, self.intf, keys, self.drv._next)
            
        return val
            
    def blk_write(self, val, keys=None):
#         val = self._write_prep(val, keys)
#         self.drv.blk_push(val)
        self.intf.blk_write(self, val)

#     def write(self, val, keys=None):
#         val = self._write_prep(val, keys)
#             
#         self._drv_write(val, 'write')

    def write_after(self, val, delay):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        self.drv.write_after(val, delay)
    
    def acquire(self):
        self.cur_val = self._channel.acquire(proxy=self)
        return self.cur_val

    def _drv_write(self, val, func, keys=None):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        if keys is None:
            val = self.conv(val)
        else:
            val = self._apply_subvalue(val, self.intf, keys, self.drv._next)
            
        getattr(self.drv, func)(val)

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

    def blk_pop(self, def_val=None, keys=None):
        if self.drv is None:
            return def_val
        else:
            return self.drv.blk_pop()

    def read(self, def_val=None):
        if self.drv is None:
            return def_val
        else:
            return self.drv.read()
        
    
   
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
           
    @property
    def driven(self):
        return self.drv is not None
            
