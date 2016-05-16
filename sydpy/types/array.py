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

# from .type_base import TypeBase
from sydpy.types._type_base import TypeBase, convlist
from sydpy import ConversionError
from sydpy.types import convgen

def Array(cls, w=((1 << 16) - 1)):
    if (cls, w) not in __array_classes:
        __array_classes[(cls, w)] = type('array', (array,), dict(dtype=cls,w=w))
        
    return __array_classes[(cls, w)] 

class array(TypeBase):
    
    dtype = None
    w = (1 << 16) - 1
    
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
    
    @classmethod
    def _from_NoneType(cls, other):
        return cls([])
       
    @classmethod
    def _rnd(cls, rnd_gen):
        size = rnd_gen.rnd_int(1, cls.w)
        
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
    
    def __getitem__(self, key):
        return self._val[key]
    
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
                    for s, o in zip(self, other):
                        if s != o:
                            return False
                    return True
                except AttributeError:
                    return False
            else:
                return False
        except TypeError:
            return False

    def _full(self):
        if (len(self._val) == self.w) and (self._val[-1]._full):
            return True
        else:
            return False

    def _empty(self):
        return len(self._val) == 0

    def _iconcat_item(self, other):
        dt_remain = None
            
        if (self._val) and (not self._val[-1]._full):
            dt_remain = self._val[-1]
            self._val.pop()
        else:
            dt_remain = self.dtype()

        for d, r in convgen(other, self.dtype, dt_remain):
            self._val.append(d)
            if self._full():
                return r

        return r
        
    def _iconcat(self, other):
        if other is Array:
            for item in other:
                self._iconcat_item(item)
        else:
            self._iconcat_item(other)
    
    @classmethod
    def _convto(cls, cls_other, val):
        convlist = []
        remain = cls_other()
        for item in val:
            for d, r in convgen(item, cls_other, remain):
                if d._full():
                    convlist.append(d)
                    remain = r
                else:
                    remain = d
        
        if (remain is not None) and (not remain._empty()):
            convlist.append(remain)
         
        conval = convlist[0]
        for item in convlist[1:]:
            conval = item._concat(conval)
        
        return conval    
#             print(convlist(cls, item))
#             for d, r in convgen(remain, item):
#                 conval._concat()
#                 self._val.append(d)
#                 if self._full():
#                     return r
#             
#             convgen(dtype(), item)
#             for item = convlist(cls, item)
#             if conval is None:
#                 conval = item
#             else:
#                 conval._concat(item)
        
        
    
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
        
            
                
    

    