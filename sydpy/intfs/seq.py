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

"""Module implements the seq interface."""

from ._intf import _Intf
from .sig import sig
from sydpy.types import convgen, bit 
from sydpy._simulator import simwait
from sydpy._util._util import arch
from sydpy._process import always
import types
from sydpy._event import Event
from sydpy.intfs._intf import IntfDir, Intf, subintfs, SlicedIntf

@arch
def _sig_to_seq_arch(self, data_i, data_o):
    data_o.valid.next = True
    data_o.last.next = True
    
    @always(self, data_o.clk.e.posedge)
    def proc():
        if data_o.ready:
            data_o.data.next = data_i
            
@arch
def _seq_to_sig_arch(self, data_i, data_o):
    @always(self, data_i.clk.e.posedge)
    def proc():
        if data_i.ready and data_i.valid:
            data_o.next = data_i.data
        
@arch
def _seq_to_tlm_arch(self, data_i, data_o):

    data_i.ready.next = True
    remain = [None]
    
    @always(self, data_i.clk.e.posedge)
    def acquire():
        nonlocal remain
        
        if data_i.valid:
            data_recv = data_i.data.read()
            data_prep = None
            
            data_conv_gen = convgen(data_recv, data_o, remain[0])

            try:
                data_prep = next(data_conv_gen)
                
                if data_i.last:
                    data_o.write(data_prep)
                
            except StopIteration as e:
                remain[0] = e.value
                
                if data_i.last:
                    data_o.write(remain[0])
                    remain[0] = None
                    pass

@arch
def _tlm_to_seq_arch(self, data_i, data_o):
    data_fifo = []
    last_fifo = []
    
    last_data_event = Event()
    data_o.last.init(0)
    data_o.valid.init(0)
    
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
                    data_fifo.append(data_o.intf._get_dtype()(remain))
                    last_fifo.append(True)
                    remain = None
                else:
                    try:
                        last_fifo[-1] = True
                    except:
                        pass
                
                
                if not data_o.valid.read(False):
                    data_o.data.next = data_fifo[0]
                    data_o.last.next = last_fifo[0]
                    data_o.valid.next = True

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

@arch
def _combine_seqs(self, data_i, data_o):
    
    valids = [elem.valid for elem in data_i]
    readys = [elem.ready for elem in data_i]
    lasts = [elem.last for elem in data_i]
    
    @always(self, data_o.ready, *valids)
    def valid_proc():
        if data_o.ready:
            all_ready = True
            
            for v in valids:
                if not v:
                    all_ready = False
                    break
        else:
            all_ready = False
                
        for r in readys:
            r.next = all_ready
            
        data_o.valid.next = all_ready
        
    @always(self, *lasts)
    def last_proc():
        any_last = False
        
        for l in lasts:
            if l:
                any_last = True
                break
            
        data_o.last.next = any_last

class seq(_Intf):
    
    _subintfs = ('clk', 'data', 'last', 'valid', 'ready')
    _intf_type_name = 'seq'
    _child_side_dict = {
                        IntfDir.slave: dict(clk=IntfDir.master, 
                                            data=IntfDir.slave,
                                            valid=IntfDir.slave,
                                            last=IntfDir.slave,
                                            ready=IntfDir.master
                                            ),
                        
                        IntfDir.master: dict(clk=IntfDir.master, 
                                            data=IntfDir.master,
                                            valid=IntfDir.master,
                                            last=IntfDir.master,
                                            ready=IntfDir.slave
                                            )
                        }
    
    def_subintf = None
    _dtype = None
    _sig = None
    
    def __init__(self, dtype=None, parent=None, name=None, init=None, module=None):
        _Intf.__init__(self, parent=parent, name=name, module=module)
        
        self.clk  = sig(bit, parent=self, name='clk')
        self.data = sig(dtype, parent=self, name='data', init=init)
        self.valid = sig(bit, parent=self, name='valid', dflt=1)
        self.ready = sig(bit, parent=self, name='ready', dflt=1)
        self.last = sig(bit, parent=self, name='last', dflt=1)
        self.last.add_source(self.valid)
       
        self.def_subintf = self.data
        self._dtype = dtype
        
        self.__create_sigout()
        
    def set_module(self, module):
        _Intf.set_module(self, module)
        self.__create_sigout()
    
    def __create_sigout(self):
        if (self._sig is None) and (self._get_dtype() is not None) and (self.get_module() is not None):
            self._sig = sig(self._get_dtype(), module=self.get_module())
            self._sig.e = self.e
            self._sig.connect(self, side=IntfDir.slave)
            self._sig.init(self.data._init)
               
    def _get_dtype(self):
        return self._dtype
               
    def add_source(self, src):
        self.s_con(**subintfs(src, ['valid', 'last', 'ready', 'data']))
                    
        self._src = [src]
        
        for e_name in self.e:
            event = getattr(src.e, e_name)
            event.subscribe(self.e[e_name])

    def init(self, val):
        self.data.init(val)
        self._sig.init(self.data._init)

    def is_driven(self):
        return self.data.is_driven()

    def _to_sig(self, val, keys=None):
        if (keys is None) and (not val is self._sig):
            val <<= self._sig
            return None, {}
        else:
            return _seq_to_sig_arch, {}

    def _from_sig(self, other):
        return _sig_to_seq_arch, {}
    
    def _to_tlm(self, other):
        return _seq_to_tlm_arch, {}
       
    def _from_tlm(self, other):
        return _tlm_to_seq_arch, {}
    
    def _from_csig(self, other):
        intf_list = []
        
        for intf in other.intfs():
            new_intf = seq(intf.elem._get_dtype(), module=self.get_module())
            new_intf.clk <<= self.clk
            try:
                new_intf <<= intf.elem
            except Exception as e:
                print(e)
            
            intf_list.append(new_intf)
            intf.parent._replace(new_intf.data, intf.key)

        self.data <<= other
                
        arch = types.MethodType(_combine_seqs,self.get_module())
        self.get_module().arch_inst(arch, data_i=Intf(*intf_list), data_o=self.slave)
        
        return None, {}
 
    def _from_generic(self, val):
        return _sig_to_seq_arch, {}
    
    def __getattr__(self, name):
        if name in self._subintfs:
            return self._subintfs[name]
        else:
            return getattr(self._sig, name)
    
    def _hdl_gen_decl(self):
        if self.data._get_dtype() is not None:
            return self.data._get_dtype()._hdl_gen_decl()
        else:
            return ''
    
    def write(self, val, keys=None):
        self.def_subintf.write(val, keys=keys)
         
    def read(self, def_val=None):
        return self._sig.read(def_val)
    
    def deref(self, key):
        subintf = SlicedIntf(self, key)
        
        setattr(subintf, 'data', self.data.deref(key))
        
        return subintf
        

