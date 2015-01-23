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

from ._intf import _Intf
from .sig import sig
from sydpy.types import ConversionError, convgen, bit 
from sydpy._simulator import simwait
from sydpy._util._util import arch
from sydpy._process import always
import types
from sydpy._event import Event
from sydpy.intfs._intf import IntfDir, ChIntfState, csig, IntfChildSide,\
    CsigIntf, Intf, subintfs, SubIntf

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
def _seq_arch(self, proxy):
    @always(self, proxy.clk.e.posedge)
    def proc():
        try:
            print("Writing to proxy: " + proxy.data.qualified_name + ", id: " + str(id(proxy)))
            proxy.data.write(proxy.drv.read())
            if 'updated' in proxy.e:
                proxy.e.updated.trigger()
        except:
            raise

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
            
            
        
# @arch
# def _tlm_to_seq_arch(self, data_i, data_o):
#     data_fifo = []
#     last_fifo = []
#     
#     @always(self)
#     def acquire():
#         remain = None
#         
#         while(1):
#             data_recv = data_i.blk_pop()
# 
#             data_conv_gen = convgen(data_recv, data_o.intf._get_dtype())
# 
#             try:
#                 while True:
#                     data_prep = next(data_conv_gen)
#                     data_fifo.append(data_prep)
#                     last_fifo.append(False)
#             except StopIteration as e:
#                 remain = e.value
#                 if remain is not None:
#                     data_fifo.append(data_o.intf._get_dtype()(remain))
#                     last_fifo.append(True)
#                     remain = None
#                 else:
#                     last_fifo[-1] = True
#             
#             if not data_o.valid:
#                 data_o.next = data_fifo[0]
#                 data_o.last.next = last_fifo[0]
#                 data_o.valid.next = True
#             
#             simwait(data_o.last.e.posedge)
# 
#     @always(self, data_o.clk.e.posedge)
#     def send():
#         if data_fifo:
#             data_o.valid.next = True
#             
#             if data_o.ready.read(True):
#                 data_o.next = data_fifo.pop(0)
#                 data_o.last.next = last_fifo.pop(0)    
#         else:
#             data_o.valid.next = False
#             data_o.last.next = False

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

class mirror(sig):

    @property
    def qualified_name(self):
        return self.parent.qualified_name()
       
    def write(self, val, keys=None):
        self._parent.write(val, keys=None)
        
    def read(self, def_val=None):
        return self._parent.read(def_val) 

def m_seq(*args, **kwargs):
    return seq(*args, direction=IntfDir.master, **kwargs)

def s_seq(*args, **kwargs):
    return seq(*args, direction=IntfDir.slave, **kwargs)

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
#         self.data.e = self.e
        self.valid = sig(bit, parent=self, name='valid', dflt=1)
        self.ready = sig(bit, parent=self, name='ready', dflt=1)
        self.last = sig(bit, parent=self, name='last', dflt=1)
        self.last.add_source(self.valid)
       
        self.def_subintf = self.data # self.subintfs['data']
        self._dtype = dtype
#         self._sig = None
        
        self.__create_sigout()
        
#         self._child_side_dict = dict(clk=IntfChildSide.slave, 
#                                      data=IntfChildSide.same,
#                                      valid=IntfChildSide.same,
#                                      last=IntfChildSide.same,
#                                      ready=IntfChildSide.flip
#                                      )
    
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
    
#     def connect(self, other, side=IntfDir.slave, **subs):
#         _Intf.connect(self, other, side, **subs)
#         if (self.get_channel() is not None):
#             self.__create_sigout()
                  
               
    def add_source(self, src):
        self.s_con(**subintfs(src, ['valid', 'last', 'ready', 'data']))
                    
#         self.clk <<= src.clk
#         self.data <<= src.data
#         self.valid <<= src.valid
#         self.ready >>= src.ready
#         self.last <<= src.last
        
        self._src = [src]
        
        for e_name in self.e:
            event = getattr(src.e, e_name)
            event.subscribe(self.e[e_name])

#         self.subintfs['clk'] = sig(bit, parent=self, name='clk')
#         self.subintfs['data'] = sig(dtype, parent=self, name='data')
#         self.subintfs['last'] = sig(bit, parent=self, name='last')
#         self.subintfs['valid'] = sig(bit, parent=self, name='valid')
#         self.subintfs['ready'] = sig(bit, parent=self, name='ready')
    
#     def assign_intf(self, other, side=IntfDir.slave):
#         if (side == IntfDir.slave) and self.intf_eq(other):
#             self.add_source(other)
#             return
#         
#         if isinstance(other, csig):
#             seq_intf_inputs = [];
#             
#             for s in other._senslist:
#                 if isinstance(s._intf, seq):
#                     seq_intf_inputs.append(s)
#                     
#             if len(seq_intf_inputs) == 1:
#                 seq_in = seq_intf_inputs[0]._intf
#                 self.valid.assign(seq_in.valid)
#                 self.last.assign(seq_in.last)
#                 self.clk.assign(seq_in.clk)
#                 seq_in.ready.assign(self.ready)
#                 self.data.assign(other)
#                 return
#             else:
#                 
#         else:
#             arch, cfg = self.conv_path(other)
#     #         self._state = ChIntfState.drv_con_wait
#             arch = types.MethodType(arch,self._module)
#             self.get_module().arch_inst(arch, data_i=other, data_o=self, **cfg)
    
    def init(self, val):
        self.data.init(val)
        self._sig.init(self.data._init)
    
#     def set_proxy(self, proxy):
#         _Intf.set_proxy(self, proxy)
#         
#         if self.last._state == ChIntfState.free:
#             self.last.assign(self.valid)
    
    def _child_state_changed(self, child):
        if child.name == 'data':
            self._state = child._state
    
    def is_driven(self):
        return self.data.is_driven()
    
#     def copy(self):
#         return seq(self.def_subintf._get_dtype(), self.parent, self.name)

    def _to_sig(self, val, keys=None):
        if (keys is None) and (not val is self._sig):
#             self.__create_sigout()
                
            val <<= self._sig
            return None, {}
        else:
            return _seq_to_sig_arch, {}
#             if (self._sig is None):
#                 self.__create_sigout()
            
#             if (not val is self._sig):
                
        
        
    
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
                        
#         seq_intf_inputs = [];
#             
#         for s in other.senslist:
#             if not s is self:
#                 if self.intf_eq(s):
#                     seq_intf_inputs.append(s)
#                 
#         if len(seq_intf_inputs) == 1:
#             seq_in = seq_intf_inputs[0]
#             
#             for intf_name in self._subintfs:
#                 if intf_name != 'data':
#                     getattr(self, intf_name).assign(getattr(seq_in, intf_name), self.get_child_side(intf_name, IntfDir.slave))
#             
# #             self.add_source(seq_in)
#             self.data <<= other
#             return None, {}
#         else:
#             return _sig_to_seq_arch, {}    
#             self.valid.assign(seq_in.valid)
#             self.last.assign(seq_in.last)
#             self.clk.assign(seq_in.clk)
#             seq_in.ready.assign(self.ready)
#             self.data.assign(other)
    
    def _from_generic(self, val):
        return _sig_to_seq_arch, {}
    
#     @property
#     def dtype(self):
#         return self.subintfs['data']
    
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
            
    
    def write(self, val, keys=None):
        self.def_subintf.write(val, keys=keys)
#         _Intf.write(self, val, keys=None)
         
    def read(self, def_val=None):
        return self._sig.read(def_val)
    
    def deref(self, key):
        subintf = SubIntf(self, key)
        
        setattr(subintf, 'data', self.data.deref(key))
        
        return subintf
        

