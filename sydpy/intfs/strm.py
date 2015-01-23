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
from sydpy._signal import SignalQueueEmpty
from ._intf import _Intf
from .sig import sig
from sydpy.types import ConversionError, convgen, bit 
from sydpy._simulator import simwait
from sydpy._util._util import arch

@arch
def _sig_to_seq_arch(self, data_i, data_o):
    @always(self, data_o.clk.e.posedge)
    def proc():
        data_o.next = data_i

@arch
def _seq_to_tlm_arch(self, data_i, data_o):

    data_i.ready.next = True
    remain = [None]
    
    @always(self, data_i.clk.e.posedge)
    def acquire():
       
        if data_i.valid:
            data_recv = data_i.read()
            data_prep = None
            
            data_conv_gen = convgen(data_recv, data_o.intf.dtype, remain[0])

            try:
                data_prep = next(data_conv_gen)
                
                if data_i.last:
                    data_o.write(data_prep)
                
            except StopIteration as e:
                remain[0] = e.value
                
                if data_i.last:
                    data_o.write(remain[0])
                    remain[0] = None


class strm(_Intf):
    
    def __init__(self, dtype=None, parent=None, name=''):

        _Intf.__init__(self, parent=parent, name=name)

        self.subintfs['data'] = sig(dtype, parent=self, name='data')
        self.subintfs['last'] = sig(bit, parent=self, name='last')
        self.subintfs['valid'] = sig(bit, parent=self, name='valid')
        self.subintfs['ready'] = sig(bit, parent=self, name='ready')
        
        self.def_subintf = self.subintfs['data']

    def idle(self, proxy):
        proxy.valid.next = False

    def push(self, proxy, data):
        proxy.valid.next = True
        
        if proxy.ready.read(True):
            proxy.data.next = data
        else:
            raise Exception

    def write(self, proxy, data):
        
#         try:
#             last = data[1]
#             data = data[0]
#         except:
#             last = True
        
        proxy.valid.next = True
        proxy.data.next = data
        
#         if proxy.ready.read(True):
#             proxy.valid.next = True
#             proxy.data.next = data
#             proxy.last.next = last
#         else:
#             raise Exception

#         print("Proxy: " + proxy.qualified_name + ", id: " + str(id(proxy)))
#         if (proxy.parent_proxy is not None):
#             print("Parent: " + proxy.parent_proxy.qualified_name  + ", id: " + str(id(proxy.parent_proxy)))        
#         print(proxy.data.drv.name)
#         print(proxy.valid.drv.name)
#         print(proxy.last.drv.name)
#         print('-------------------------')
#         
#         pass
#         
    def read(self, proxy, def_val):
        if proxy.valid.read(True):
            return (proxy.data.read(def_val), proxy.last.read())
        else:
            raise Exception
    
    @property
    def dtype(self):
        return self.data.dtype
    
    def deref(self, key):
        asp_copy = copy(self)
        asp_copy.data.dtype = self.data.dtype.deref(key)
        
        return asp_copy
    
    def __str__(self):
        return "strm"

