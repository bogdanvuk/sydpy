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

"""Module that implements array sydpy type."""

__array_classes = {}

from ._type_base import TypeBase
from sydpy import ConversionError
from sydpy.types import convgen

def Array(cls, max_size=((1 << 16) - 1)):
    if (cls, max_size) not in __array_classes:
        __array_classes[(cls, max_size)] = type('array', (array,), dict(dtype=cls,max_size=max_size))
        
    return __array_classes[(cls, max_size)] 

class array(TypeBase):
    
    dtype = None
    max_size = (1 << 16) - 1
    
    def __init__(self, val=[]):
        
        self._val = []
        
        for v in val:
            self._val.append(self.dtype(v))

    def _replace(self, key, val):
        if isinstance( key, slice ) :
            high = max(key.start, key.stop)
            low = min(key.start, key.stop)
            
            for key in range(low, high + 1):
                self._val[key] = self.dtype(val[key - low])
        elif isinstance( key, int ) :
            self._val[key] = self.dtype(val)
        else:
            raise TypeError("Invalid argument type.")
    
    def _full(self):
        return False
       
    @classmethod
    def _rnd(cls, rnd_gen):
        size = rnd_gen.rnd_int(1, cls.max_size)
        
        val = [rnd_gen._rnd(cls.dtype) for _ in range(size)] 
        
        return cls(val)
    
    def _hdl_gen_ref(self, conv):
        s = conv._hdl_gen_ref(self._val[0])

        if len(self._val) > 1:
            s += ", "
            for e in self._val[1:]:
                s += conv._hdl_gen_ref(e)
                
            s = "'{" + s + "}"
            
        return s
    
    def __len__(self):
        return len(self._val)
    
    def __iadd__(self, other):
        for v in other:
            self._val.append(self.dtype(v))
            
        return self
    
    @classmethod
    def _hdl_gen_decl(cls):
        pass
        
    @classmethod
    def _hdl_gen_call(cls, conv=None, node=None):
        args = []
        for a in node.args:
            args.append(conv.obj_by_node(a))
            
        a = cls(args)
        
        return a._hdl_gen_ref(conv)
    
    @classmethod
    def deref(self, key):
        return self.dtype

    def __str__(self):
        return "[" + ",".join([str(e) for e in self._val]) + "]"
    
    __repr__ = __str__
    
    @classmethod
    def cls_eq(cls, other):
        return cls.dtype == other.dtype
    
    def __iter__(self):
        return iter(self._val)
    
    def __eq__(self, other):
        try:
            if len(self) == len(other):
                try:
                    for s, o in zip(self._val, other._val):
                        if s != o:
                            return False
                    return True
                except AttributeError:
                    return False
            else:
                return False
        except TypeError:
            return False
    
    def _icon(self, other):

        dt_remain = None
            
        if self._val:
            if not self._val[-1]._full:
                dt_remain = self._val[-1]

        val = self._val.copy()
        
        data_conv_gen = convgen(other, self.dtype, dt_remain)

        while True:
            try:
                data_prep = next(data_conv_gen)
                val.append(data_prep)
            except StopIteration as e:
                if e.value is not None:
                    val.append(self.dtype(e.value))
                break
                
        new_self = self.__class__(val)

        return (new_self, None)
        
            
                
    

    