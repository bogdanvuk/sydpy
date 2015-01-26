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

"""Module that implements vector sydpy type."""

__vector_classes = {}

from ._type_base import TypeBase
from sydpy import ConversionError

def Vector(w, cls):
    if cls not in __vector_classes:
        __vector_classes[(w, cls)] = type('vector', (vector,), dict(dtype=cls, w=w))
        
    return __vector_classes[(w, cls)]

class vector(TypeBase):
    
    dtype = None
    w = 1
    
    def __init__(self, val=[]):
        
        self._val = []
        self._vld = []
        
        for _, a in zip(range(self.w), val):
            val = self.dtype(a)
            self._val.append(val)
            self._vld.append(val._full())
            
        for _ in range(len(self._val), self.w):
            self._val.append(self.dtype())
            self._vld.append(False)

    def _replace(self, key, val):
        if isinstance( key, slice ) :
            high = max(key.start, key.stop)
            low = min(key.start, key.stop)
        
            if high >= self.w:
                raise IndexError("The index ({0}) is out of range.".format(key))
            
            val = self._val.copy()
            
            for key in range(low, high + 1):
                val[key] = self.dtype(val[key - low])
        elif isinstance( key, int ) :
            if high >= self.w:
                raise IndexError("The index ({0}) is out of range.".format(key))
            
            val = self._val.copy()
            
            val[key] = self.dtype(val)
        else:
            raise TypeError("Invalid argument type.")
        
        return self.__class__(*val)
    
    def _hdl_gen_ref(self, conv):
        s = conv._hdl_gen_ref(self._val[0])

        if len(self._val) > 1:
            s += ", "
            for e in self._val[1:]:
                s += conv._hdl_gen_ref(e)
                
            s = "'{" + s + "}"
            
        return s
    
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

    def __len__(self):
        return self.w

    def __str__(self):
        return "(" + ",".join([str(e) for e in self._val]) + ")"
    
    __repr__ = __str__
    
    def __iter__(self):
        return iter(self._val)
    
    def __reversed__(self):
        return reversed(self._val)
    
    def _full(self):
        for u in self._vld:
            if not u:
                return False
        
        return True
    
    @classmethod
    def _rnd(cls, rnd_gen):
        val = [rnd_gen._rnd(cls.dtype) for _ in range(cls.w)] 
        
        return cls(val)
    
    def _icon(self, other):
        
        for i, u in reversed(list(enumerate(self._vld))):
            if u:
                last_unset = i + 1
                break
        else:
            last_unset = 0
            
        if last_unset >= len(self):
            return (None, other)
        
        dt_remain = self._val[last_unset]

        remain = other
        val = self._val.copy()
        conv_gen = self.dtype._convgen(remain, dt_remain)
        
        while last_unset < len(self):
            try:
                data, remain = next(conv_gen)
                val[last_unset] = data
                last_unset += 1
            except StopIteration as e:
                remain = e.value
                if remain is not None:    
                    if last_unset < len(self):
                        val[last_unset] = remain
                        remain = None
                break

        new_self = self.__class__(val)

        return (new_self, remain)
                
    

    