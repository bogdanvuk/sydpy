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
from ._intf import Intf

def _sig_to_seq_arch(self, clk, data_i, data_o):
    @always(self, clk.e.posedge)
    def proc():
        data_o.next = data_i

class sig(Intf):
    
    def __init__(self, dtype=None, parent=None, name=''):
        Intf.__init__(self, parent=parent, name=name)
        self.dtype = dtype
    
    def __seq__(self, val):
        return _sig_to_seq_arch
    
    def __str__(self):
        
        name = self.name
        dt_name = ''
        
        try:
            if not self.dtype.__name__.startswith('bit'):
                dt_name = self.dtype.__name__
            else:
                name = self.name
        except AttributeError:
            dt_name = str(self.dtype)

        if name:
            if dt_name:
                name = name + '_' + dt_name
        else:
            name = dt_name

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
        return sig(self.dtype.deref(key))
    
    __repr__ = __str__
    
    def __eq__(self, other):
        if isinstance(other, sig):
            if self.name == other.name:
                if (self.dtype is None) or (other.dtype is None):
                    return True
                else:
                    return (self.dtype == other.dtype)

        return False
