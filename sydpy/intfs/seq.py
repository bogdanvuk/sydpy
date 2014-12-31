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
from ._intf import Intf
from .sig import sig
from sydpy.types import ConversionError, convgen, bit 
from sydpy._simulator import simwait
from sydpy._util._util import architecture

@architecture
def _sig_to_seq_arch(self, data_i, data_o):
    @always(self, data_o.clk.e.posedge)
    def proc():
        data_o.next = data_i

@architecture
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
            
            
        
@architecture
def _tlm_to_seq_arch(self, data_i, data_o):
    data_fifo = []
    last_fifo = []
    
    @always(self)
    def acquire():
        remain = None
        
        while(1):
            data_recv = data_i.blk_pop()

            data_conv_gen = convgen(data_recv, data_o.intf.dtype)

            try:
                while True:
                    data_prep = next(data_conv_gen)
                    data_fifo.append(data_prep)
                    last_fifo.append(False)
            except StopIteration as e:
                remain = e.value
                if remain is not None:
                    data_fifo.append(data_o.intf.dtype(remain))
                    last_fifo.append(True)
                    remain = None
                else:
                    last_fifo[-1] = True
            
            if not data_o.valid:
                data_o.next = data_fifo[0]
                data_o.last.next = last_fifo[0]
                data_o.valid.next = True
            
            simwait(data_o.last.e.posedge)

    @always(self, data_o.clk.e.posedge)
    def send():
        if data_fifo:
            data_o.valid.next = True
            
            if data_o.ready.read(True):
                data_o.next = data_fifo.pop(0)
                data_o.last.next = last_fifo.pop(0)    
        else:
            data_o.valid.next = False
            data_o.last.next = False

class seq(Intf):
    
    def __init__(self, dtype=None, parent=None, name=''):
        Intf.__init__(self, parent=parent, name=name)
        
        self.subintfs['clk'] = sig(bit, parent=self, name='clk')
        self.subintfs['data'] = sig(dtype, parent=self, name='data')
        
#         self.subintfs['last'] = sig(bit, parent=self, name='last')
#         self.subintfs['valid'] = sig(bit, parent=self, name='valid')
#         self.subintfs['ready'] = sig(bit, parent=self, name='ready')
#         self.subintfs['clk'] = sig(bit, parent=self, name='clk')
        
        self.def_subintf = 'data'

    def _to_sig(self, val):
        pass
    
    def _from_sig(self, val):
        yield _sig_to_seq_arch, {}
    
    def _to_tlm(self, val):
        yield _seq_to_tlm_arch, {}
       
    def _from_tlm(self, val):
        yield _tlm_to_seq_arch, {}
    
    @property
    def dtype(self):
        return self.data.dtype
    
    def __str__(self):
        name = 'seq_'
        
        if self.data.dtype is not None:
            try:
                name += self.data.dtype.__name__
            except AttributeError:
                name += str(self.data.dtype)
            
#         if self.clk is not None:
#             name += ',' + str(self.clk) 

        return name
    
    __repr__ = __str__
    
    def _hdl_gen_decl(self):
        if self.data.dtype is not None:
            return self.data.dtype._hdl_gen_decl()
        else:
            return ''
    
    def deref(self, key):
        asp_copy = copy(self)
        asp_copy.data.dtype = self.data.dtype.deref(key)
        
        return asp_copy

