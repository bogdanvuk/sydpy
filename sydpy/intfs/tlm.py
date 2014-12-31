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
from ._intf import Intf
from sydpy._util._util import architecture
from sydpy.types import convgen

@architecture
def _tlm_to_tlm_arch(self, data_i, data_o):

    remain = [None]
    
    @always_acquire(self, data_i)
    def acquire(data_recv):
       
        data_conv_gen = convgen(data_recv, data_o.intf.dtype, remain[0])

        try:
            data_prep = next(data_conv_gen)
            data_o.write(data_prep)
        except StopIteration as e:
            remain[0] = e.value
            data_o.write(remain[0])
            remain[0] = None


@architecture
def _tlm_to_sig_arch(self, data_i, data_o):
    
    @always(self, data_i.e.enqueued)
    def proc():
        data_o.next = data_i.pop()

class tlm(Intf):
    
    def __init__(self, dtype=None, parent=None, name=''):
        Intf.__init__(self, parent=parent, name=name)
        
        self.dtype = dtype
    
    def _from_tlm(self, val):
        yield _tlm_to_tlm_arch, {}
        
    def _to_sig(self, val):
        yield _tlm_to_sig_arch, {}
    
    def _from_sig(self, val):
        pass
        
    def __str__(self):
        name = 'tlm_'
        
        if self.dtype is not None:
            try:
                name += self.dtype.__name__
            except AttributeError:
                name += str(self.dtype)
            
#         if self.clk is not None:
#             name += ',' + str(self.clk) 

        return name
    
    def _rnd(self, rnd_gen):
        try:
            return rnd_gen._rnd(self.dtype)
        except TypeError:
            return None
            
    def _hdl_gen_decl(self):
        if self.dtype is not None:
            return self.dtype._hdl_gen_decl()
        else:
            return ''
    
    def deref(self, key):
        asp_copy = copy(self)
        asp_copy.dtype = self.dtype.deref(key)
        
        return asp_copy
    
    __repr__ = __str__
