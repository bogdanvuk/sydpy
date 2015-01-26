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

"""Module implements the sig interface."""

from ._intf import _Intf
from sydpy._signal import Signal
from sydpy._process import always
from sydpy.extens.tracing import VCDTrace, VCDTraceMirror
from sydpy._util._util import arch
from sydpy import ConversionError
from sydpy._simulator import simwait
from sydpy.intfs._intf import SlicedIntf

@arch
def _sig_to_sig_arch(self, data_i, data_o):
    @always(self, data_i)
    def proc():
        data_o.next = data_i

class sig(_Intf):
    _intf_type_name = 'sig'
   
    def __init__(self, dtype=None, parent=None, name=None, init=None, module=None, dflt=None):
        _Intf.__init__(self, parent=parent, name=name, module=module)
        
        self._dtype = dtype
        self._drv = None
        self._dflt = dflt
        
        self.init(init)
    
    def _get_dtype(self):
        return self._dtype
    
    def _rnd(self, rnd_var):
        return rnd_var._rnd(self._get_dtype())
    
    def init(self, val):
        if val is not None:
            self._write('write', val)
            
        self._init = val
    
    def _convgen(self, other, remain=None):
        return self._get_dtype()._convgen(other, remain)
    
    def _apply_subvalue(self, val, keys, old_val):
        """Update only part of composite data type's value."""
        if keys is not None:
            try:
                old_val = old_val._replace(keys, val)
            except AttributeError:
                old_val = self.conv(None)
                old_val = old_val._replace(keys, val)
                
            val = old_val
                    
        return val
    
    def _get_qualified_name(self):
        if self._get_dtype() is not None:
            try:
                dtype_name = '(' + self._get_dtype().__name__ + ')'
            except AttributeError:
                dtype_name = '(' + str(self._get_dtype()) + ')'
        else:
            dtype_name = ''
        
        return _Intf._get_qualified_name(self) + dtype_name
    
    def conv(self, other):
        try:
            _Intf.conv(self, other)
        except ConversionError:
            return self._get_dtype().conv(other)

    def intf_eq(self, other):
        if _Intf.intf_eq(self, other):
            if self._get_dtype().cls_eq(other._get_dtype()):
                return True

        return False
    
    def trace_val(self, name=None):
        return self.read(None)
    
    def _to_sig(self, val):
        return _sig_to_sig_arch, {}
    
    def _from_csig(self, other):
        for intf in other.intfs():
            new_intf = sig(intf.elem._get_dtype(), module=self.get_module())
            new_intf <<= intf.elem

            intf.parent._replace(new_intf, intf.key)
                
        return _sig_to_sig_arch, {}

    def _hdl_gen_decl(self):
        if self._get_dtype() is not None:
            return self._get_dtype()._hdl_gen_decl()
        else:
            return ''
    
    def deref(self, key):
        return SlicedIntf(self, key)
    
#     __repr__ = __str__
        
    def add_source(self, src):
        _Intf.add_source(self, src)

        # If tracing is enabled
        try:
            if self.get_base_channel() is not None:
                if self.get_base_channel() != src.get_base_channel():
                    self._trace = VCDTraceMirror(self.qualified_name, self) 
                    self.get_base_channel().register_traces([self._trace])
        except KeyError:
            pass
    
    def _get_base_trace(self):
        if self.is_driven():
            return self._trace
        elif self.is_sourced():
            return self._src[0]._get_base_trace()
        else:
            return None 
    
    def setup_driver(self):
        if self._drv is None:
            try:
                val = self.conv(self._dflt)
            except (ConversionError, AttributeError):
                val = None
                
            self._drv = Signal(val=val, event_set = self.e)
            
            # If tracing is enabled
            try:
                self._trace = VCDTrace(self.qualified_name, self, init=val)
                
                if self.get_base_channel() is not None:
                    self.get_base_channel().register_traces([self._trace])
            except KeyError:
                pass
                
            self.e.connected.trigger()
  
    def _write_prep(self, val, keys=None):
        if self._drv is None:
            self.setup_driver()
        
        try:
            val = val.read()
        except AttributeError:
            pass
        
        try:
            if keys is None:
                val = self.conv(val)
            else:
                val = self._apply_subvalue(val, self.intf, keys, self._drv._next)
        except AttributeError:
            pass
            
        return val
    
    def _write(self, func, val, keys=None):
        if self._drv is None:
            self.setup_driver()
        
        try:
            val = val.read()
        except AttributeError:
            pass
        
        try:
            if keys is None:
                val = self.conv(val)
            else:
                val = self._apply_subvalue(val, keys, self._drv._next)
        except AttributeError:
            pass
            
        getattr(self._drv, func)(val)
                    
    def write(self, val, keys=None):
        self._write('write', val, keys)
            
    def blk_write(self, val, keys=None):
        self._write('blk_write', val, keys)

    def write_after(self, val, delay):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        self._drv.write_after(val, delay)
    
    def acquire(self):
        self._cur_val = self._channel.acquire(proxy=self)
        return self._cur_val

    def _drv_write(self, val, func, keys=None):
        try:
            val = val.read()
        except AttributeError:
            pass
        
        if keys is None:
            val = self.conv(val)
        else:
            val = self._apply_subvalue(val, self.intf, keys, self._drv._next)
            
        getattr(self._drv, func)(val)

    def pop(self):
        if self._drv is not None:
            self._cur_val = self._drv.pop()
        else:
            self._cur_val = self._channel.pop(proxy=self)
            
        if self._cur_val is None:
            if self.init is not None:
                self._cur_val = self.init
            else:
                self._cur_val = self.intf()
            
        return self._cur_val

    def _src_read(self, func, keys=None):
        conv_val = self._cur_val
        
        for proxy in self._src:
            val = getattr(proxy, func)()
            
            if keys is not None:
                conv_val = self._apply_value(val, keys, conv_val)
            else:
                conv_val = val
                
        return conv_val

    def _read(self, func, def_val=None, keys=None):
        if func.startswith('blk_'):
            if not self.is_driven() and not self.is_sourced(): 
                simwait(self.e.connected)            
            
        if self.is_driven():
            self._cur_val = getattr(self._drv, func)()
        elif self.is_sourced():
            self._cur_val = self._src_read(func)
        elif self._dflt is not None:
            self._cur_val = self.conv(self._dflt)
        else:
            self._cur_val = def_val
                    
        return self._cur_val

