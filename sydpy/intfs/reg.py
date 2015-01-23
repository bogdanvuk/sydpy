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
from sydpy._signal import SignalQueueEmpty, Signal
from ._intf import _Intf
from .sig import sig
from sydpy.types import ConversionError, convgen, bit 
from sydpy._simulator import simwait
from sydpy._util._util import architecture
import types
from sydpy._event import Event

@arch_def
def _sig_to_reg_arch(self, data_i, data_o):
    @always(self, data_o.clk.e.posedge)
    def proc():
        data_o.next = data_i

@arch_def
def _tlm_to_seq_arch(self, data_i, data_o):
    data_fifo = []
    last_fifo = []
    
    last_data_event = Event()
    cur_val = [None, None]
    
    @always(self)
    def acquire():
        remain = None
        
        while(1):
            data_recv = data_i.blk_pop()

            data_conv_gen = convgen(data_recv, data_o)

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
                
                
                if not data_o.valid.read(False):
#                     cur_val = [data_fifo.pop(0), last_fifo.pop(0)]
                
                    data_o.data.next = data_fifo[0]
                    data_o.last.next = last_fifo[0]
                    data_o.valid.next = True
            
#             for d in zip(data_fifo, last_fifo):
#                 data_o.blk_write(d)
            
#             if not data_o.valid:
#                 data_o.next = data_fifo[0]
#                 data_o.last.next = last_fifo[0]
#                 data_o.valid.next = True
            
                simwait(last_data_event)

    @always(self, data_o.clk.e.posedge)
    def send():
        if data_fifo:
            if data_o.ready.read(True):
                if last_fifo[0]:
                    last_data_event.trigger()
                
                data_fifo.pop(0)
                last_fifo.pop(0)
                
                if data_fifo:
                    data_o.valid.next = True    
                    data_o.data.next = data_fifo[0]
                    data_o.last.next = last_fifo[0]
                else:
                    data_o.valid.next = False
                    data_o.last.next = False
        else:
            data_o.last.next = False
            data_o.valid.next = False

class mirror(sig):

    @property
    def qualified_name(self):
        return self.parent.qualified_name()
       
    def write(self, val, keys=None):
        self._parent.write(val, keys=None)
        
    def read(self, def_val=None):
        return self._parent.read(def_val) 

class seq(_Intf):
    
    _subintfs = ('clk', 'data', 'last', 'valid', 'ready')
    def_subintf = None
    
    def __init__(self, dtype=None, parent=None, name=None):
        _Intf.__init__(self, parent=parent, name=name)
        
        self.clk  = sig(bit, parent=self, name='clk')
        self.data = sig(dtype, parent=self, name='data')
        self.data.e = self.e
        self.last = sig(bit, parent=self, name='last')
        self.valid = sig(bit, parent=self, name='valid')
        self.ready = sig(bit, parent=self, name='ready')
       
        self.def_subintf = self.data # self.subintfs['data']

#         self.subintfs['clk'] = sig(bit, parent=self, name='clk')
#         self.subintfs['data'] = sig(dtype, parent=self, name='data')
#         self.subintfs['last'] = sig(bit, parent=self, name='last')
#         self.subintfs['valid'] = sig(bit, parent=self, name='valid')
#         self.subintfs['ready'] = sig(bit, parent=self, name='ready')
    
    def is_driven(self):
        return self.data.is_driven()
    
    @property
    def drv(self):
        return self.def_subintf.drv
    
    def copy(self):
        return seq(self.def_subintf._get_dtype(), self.parent, self.name)

    def _to_sig(self, val):
        pass
    
    def _from_sig(self, val):
        return _sig_to_seq_arch, {}
    
    def _to_tlm(self, val):
        return _seq_to_tlm_arch, {}
       
    def _from_tlm(self, val):
        return _tlm_to_seq_arch, {}
    
#     @property
#     def dtype(self):
#         return self.subintfs['data']
    
    def __getattr__(self, name):
        if name in self._subintfs:
            return self._subintfs[name]
        else:
            return getattr(self.def_subintf, name)
    
    def _hdl_gen_decl(self):
        if self.data.dtype is not None:
            return self.data.dtype._hdl_gen_decl()
        else:
            return ''
    
    def _child_proxy_con(self, child=None):
        if child.name == 'data':
            if self.proxy is not None:
                for e_name in self.proxy.e:
                    event = getattr(child.proxy.e, e_name)
                    event.subscribe(self.proxy.e[e_name])
                    
#     def set_proxy(self, proxy):
#         _Intf.set_proxy(self, proxy)
#         
#         if self.def_subintf.proxy is not None:
#             for e_name in self.proxy.e:
#                 event = getattr(self.def_subintf.proxy.e, e_name)
#                 event.subscribe(self.proxy.e[e_name])
        
            
#             if self.sourced:
#                 self.channel.connect_proxies_to_source(self)

#     def _state_sourced(self, child=None):
#         if self.parent is None:
#             if self.sourced:
#                 self.channel.connect_proxies_to_source(self)
#             
#     _state_driven = _state_sourced
#     _state_drv_con_wait = _state_sourced
            
    
#     def write(self, val, keys=None):
#         _Intf.write(val, keys=None)
#         
#     def read(self, def_val=None):
#         return self.def_subintf.read(def_val)
    
    def deref(self, key):
        asp_copy = copy(self)
        asp_copy.data.dtype = self.data.dtype.deref(key)
        
        return asp_copy

