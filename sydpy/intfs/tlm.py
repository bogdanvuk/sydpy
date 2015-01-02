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
from sydpy import always, always_acquire
from ._intf import Intf#, ChIntfState
from sydpy._util._util import architecture
from sydpy.types import convgen
from sydpy._signal import Signal
from sydpy.extens.tracing import VCDTrace

@architecture
def _tlm_to_tlm_arch(self, data_i, data_o):

    remain = [None]
    
    @always_acquire(self, data_i)
    def acquire(data_recv):
       
        data_conv_gen = convgen(data_recv, data_o.def_subintf, remain[0])

        try:
            data_prep = next(data_conv_gen)
            data_o.write(data_prep)
        except StopIteration as e:
            remain[0] = e.value
            data_o.write(remain[0])
            remain[0] = None


@architecture
def _tlm_to_sig_arch(self, data_i, data_o):
    
    @always_acquire(self, data_i)
    def proc(val):
        data_o.next = val

class tlm(Intf):
    
    _subintfs = ('data', )
    
    def __init__(self, dtype=None, parent=None, name=None):
        self.data = dtype
        self.def_subintf = dtype
        self.drv = None
        
        Intf.__init__(self, parent=parent, name=name)
    
    @property
    def qualified_name(self):
        if self.def_subintf is not None:
            try:
                dtype_name = '(' + self.def_subintf.__name__ + ')'
            except AttributeError:
                dtype_name = '(' + str(self.def_subintf) + ')'
        
        return Intf.qualified_name.fget(self) + dtype_name
        
#         if self.proxy._channel is not None:
#             return self.proxy._channel.name + '.' + self.qualif_intf_name + dtype_name
#         else:
#             return self.qualif_intf_name + dtype_name
    
    def copy(self):
        return tlm(self.def_subintf, self.parent, self.name)
    
    def trace_val(self, name=None):
        return self.read()
    
    def _from_tlm(self, val):
        return _tlm_to_tlm_arch, {}
        
    def _to_sig(self, val):
        return _tlm_to_sig_arch, {}
    
    def _from_sig(self, val):
        pass
    
    def _write_prep(self, val):
        if self.drv is None:
            self.drv = Signal(val=self.def_subintf(), event_set = self.proxy.e)
            
            self.proxy._register_traces([VCDTrace(self.qualified_name, self)])
       
        return self.def_subintf.conv(val)
    
    def blk_write(self, val):
        val = self._write_prep(val)
        self.drv.blk_push(val)
    
    def write(self, val):
        val = self._write_prep(val)
        self.drv.push(val)

       
    def _rnd(self, rnd_gen):
        try:
            return rnd_gen._rnd(self.def_subintf)
        except TypeError:
            return None
            
    def _hdl_gen_decl(self):
        if self.def_subintf is not None:
            return self.def_subintf._hdl_gen_decl()
        else:
            return ''
    
    def deref(self, key):
        asp_copy = copy(self)
        asp_copy.dtype = self.def_subintf.deref(key)
        
        return asp_copy
    
#     __repr__ = __str__
