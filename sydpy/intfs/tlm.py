#  This file is part of sydpy.
# 
#  Copyright (C) 2014-2015 Bogdan Vukobratovic
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

"""Module implements the tlm interface."""

from sydpy import always_acquire
from sydpy._util._util import arch
from sydpy.types import convgen
from sydpy.intfs._intf import IntfDir
from sydpy.intfs import sig

@arch
def _tlm_to_tlm_arch(self, data_i, data_o):

    remain = [None]
    
    @always_acquire(self, data_i)
    def acquire(data_recv):
       
        data_conv_gen = convgen(data_recv, data_o._get_dtype(), remain[0])

        try:
            data_prep = next(data_conv_gen)
            data_o.write(data_prep)
        except StopIteration as e:
            remain[0] = e.value
            data_o.write(remain[0])
            remain[0] = None


@arch
def _tlm_to_sig_arch(self, data_i, data_o):
    
    @always_acquire(self, data_i)
    def proc(val):
        data_o.next = val

def m_tlm(*args, **kwargs):
    return tlm(*args, direction=IntfDir.master, **kwargs)

def s_tlm(*args, **kwargs):
    return tlm(*args, direction=IntfDir.slave, **kwargs)

class tlm(sig):
    _intf_type_name = 'tlm'
    
    def __init__(self, dtype=None, parent=None, name=None, module=None):
        sig.__init__(self, dtype=dtype, parent=parent, name=name, module=module)
    
    def _from_tlm(self, val):
        return _tlm_to_tlm_arch, {}
        
    def _to_sig(self, val):
        return _tlm_to_sig_arch, {}
    
    def _from_sig(self, val):
        pass
    
    def blk_write(self, val, keys=None):
        self._write('blk_push', val, keys)
    
    def write(self, val, keys=None):
        self._write('blk_push', val, keys)

    def _hdl_gen_decl(self):
        if self.def_subintf is not None:
            return self.def_subintf._hdl_gen_decl()
        else:
            return ''
