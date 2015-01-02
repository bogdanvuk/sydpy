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

from copy import copy
from sydpy._process import always
from ._intf import Intf#, ChIntfState
from sydpy._signal import Signal
from sydpy.extens.tracing import VCDTrace
# from sydpy._ch_proxy import ChIntfState

def _sig_to_seq_arch(self, clk, data_i, data_o):
    @always(self, clk.e.posedge)
    def proc():
        data_o.next = data_i

class sig(Intf):
    _subintfs = ('data', )
    
    def __init__(self, dtype=None, parent=None, name=''):
        self.def_subintf = dtype
        self.data = dtype
        self.drv = None
        
        Intf.__init__(self, parent=parent, name=name)
#         self.subintfs['data'] = dtype
    
    @property
    def qualified_name(self):
        try:
            return self.def_subintf.qualified_name
        except AttributeError:
            if self.def_subintf is not None:
                try:
                    dtype_name = '(' + self.def_subintf.__name__ + ')'
                except AttributeError:
                    dtype_name = '(' + str(self.def_subintf) + ')'
            
            if self.proxy._channel is not None:
                return self.proxy._channel.name + '.' + self.qualif_intf_name + dtype_name
            else:
                return self.qualif_intf_name + dtype_name
    
    def copy(self):
        return sig(self.def_subintf, self.parent, self.name)
    
    def trace_val(self, name=None):
        return self.read(None)
    
    def __seq__(self, val):
        return _sig_to_seq_arch
    
    def _fullname(self):
        name = ''
        if self.parent is not None:
            name = self.parent._fullname() + '_'
        
        if self._channel is not None:
            name += self._channel.name + '_'
        
        if name:
            name += self.name + '_'
        
        try:
            name += self.def_subintf.__name__
        except AttributeError:
            name += str(self.def_subintf)
        
        return name
    
    def __str__(self):
        if self.def_subintf is not None:
            try:
                name = self.def_subintf.__name__
            except AttributeError:
                name = str(self.def_subintf)
        else:
            name = self.name
            
#         if self.clk is not None:
#             name += ',' + str(self.clk) 

        return name
    
    def _rnd(self, rnd_gen):
        try:
            return rnd_gen._rnd(self.def_subintf)
        except TypeError:
            return None
            
    def _hdl_gen_decl(self):
        if self.dtype is not None:
            return self.dtype._hdl_gen_decl()
        else:
            return ''
    
    def deref(self, key):
        return sig(self.def_subintf.deref(key), keys=key)
    
#     __repr__ = __str__
     
    def __getattr__(self, name):
        return getattr(self.def_subintf, name)
    
    def setdrv(self, drv):
        self.drv = drv
    
    def blk_pop(self, def_val=None):
        try:
            return self.def_subintf.blk_pop(def_val)
        except AttributeError:
            if self.drv is None:
                return def_val
            else:
                return self.drv.blk_pop()
            
    def read(self, def_val=None):
        try:
            self.def_subintf.read(def_val)
        except AttributeError:
            if self.drv is None:
                return def_val
            else:
                return self.drv.read()
            
    
    def write(self, val, keys=None):
        try:
            self.def_subintf.write(val)
        except AttributeError:
            Intf.write(self, val, keys)
        
#     def read(self, def_val=None):
#         if self.drv is not None:
#             return self.drv.read()
#         else:
#             if self.parent is None:
#                 return self.channel.read(proxy=self, def_val=def_val)
#             else:
#                 return def_val
    
#     def __eq__(self, other):
#         if isinstance(other, sig):
#             if self.name == other.name:
#                 if (self.dtype is None) or (other.dtype is None):
#                     return True
#                 else:
#                     return (self.dtype == other.dtype)
# 
#         return False
