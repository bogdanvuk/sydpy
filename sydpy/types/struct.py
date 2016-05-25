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

"""Module that implements struct sydpy type."""

__struct_classes = {}

from sydpy.types._type_base import TypeBase, convgen, convlist, conv
from sydpy import ConversionError
from collections import OrderedDict
from itertools import islice

def Struct(*args):
    vals = []
    names = []
    for a in args:
        names.append(a[0])
        vals.append(a[1])
    
#     s_tuple = tuple(names)    
    dtype=OrderedDict(list(zip(names, vals)))
    
    if args not in __struct_classes:
        __struct_classes[args] = type('struct', (struct,), dict(dtype=dtype))
        
    return __struct_classes[args]

class struct(TypeBase):
    
    dtype = None
    
    def __init__(self, val=[]):
        
        if not val:
            val = []
        
        self._val = []
        self._vld = []
        
        for t, a in zip(self.dtype, val):
            val = self.dtype[t](a)
            self._val.append(val)
            try:
                self._vld.append(val._full())
            except AttributeError:
                self._vld.append(True)
            
        for (_,t) in islice(self.dtype.items(), len(self._val), len(self.dtype)):
            d = t()    
            self._val.append(d)
            try:
                self._vld.append(d._full())
            except AttributeError:
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
        
        return self.__class__(val)
    
    def _hdl_gen_ref(self, val):
        s = val._hdl_gen_ref(self._val[0])

        if len(self._val) > 1:
            s += ", "
            for e in self._val[1:]:
                s += val._hdl_gen_ref(e)
                
            s = "'{" + s + "}"
            
        return s
    
    @classmethod
    def _hdl_gen_decl(cls):
        pass
        
    @classmethod
    def _hdl_gen_call(cls, val=None, node=None):
        args = []
        for a in node.args:
            args.append(val.obj_by_node(a))
            
        a = cls(*args)
        
        return a._hdl_gen_ref(val)
    
    @classmethod
    def deref(self, key):
        return self.dtype[key]

    def __str__(self):
        return "(" + ",".join([str(e) for e in self._val]) + ")"
    
    __repr__ = __str__
    
#     def __next__(self):
#         return next(iter(self.val))
    
    def __iter__(self):
        return iter(self._val)
    
    def __len__(self):
        return len(self.dtype)
    
    def _full(self):
        for u in self._vld:
            if not u:
                return False
        
        return True
    
    def __getattr__(self, key):
        try:
            if key in self.dtype.keys():
                return self._val[list(self.dtype.keys()).index(key)]
            else:
                return super().__getattribute__(key)
        except ValueError:
            raise AttributeError
        
#     def __setattr__(self, key, val):
#         try:
#             self._val[list(self.dtype.keys()).index(key)] = val
#         except ValueError:
#             raise AttributeError        
    
    def __getitem__(self, key):
        if isinstance( key, slice ) :
            st = Struct(*islice(self.dtype.items(), key.start, key.stop))
            
            return st(list(self._val[key]))
        elif isinstance( key, int ) :
            return self._val[key]
        elif isinstance(key, str):
            pos = list(self.dtype.keys()).index(key)
            return self._val[pos]
        else:
            raise TypeError("Invalid argument type.")

    def __contains__(self, key):
        return key in self.dtype.keys()

    def __setitem__(self, key, val):
        if isinstance( key, int ) :
            self._val[key] = val
        elif isinstance(key, str):
            pos = list(self.dtype.keys()).index(key)
            self._val[pos] = val
    
#     @classmethod
#     def _from_NoneType(cls, other):
#         return cls()
    
    @classmethod
    def _from_struct(cls, other):
        if cls.dtype is other.dtype:
            s = cls()
            for i, (val, vld) in enumerate(zip(other._val, other._vld)):
                s._val[i] = val
                s._vld[i] = vld
                
            return s
        else:
            raise ConversionError
    
    @classmethod
    def _from_dict(cls, other):
        s = cls()
        for k,v in other.items():
            try:
                i = list(s.dtype.keys()).index(k)
            except ValueError:
                raise ConversionError
            
            s._val[i] = v
            s._vld[i] = True
            
        return s
            
#             s[k] = v
#         if cls.w == other.w:
#             return other
#         else:
#             raise ConversionError
    
    @classmethod
    def _rnd(cls, rnd_gen):
        val = [rnd_gen._rnd(cls.dtype[t]) for t in cls.dtype] 
        
        return cls(val)
    
    
    def _iconcat(self, other):
        dt_remain = other
        for i, v in enumerate(self._val):
            if not v._full():
                for d, r in convgen(dt_remain, v.__class__, v):
                    if d._full():
                        self._val[i] = d
                        self._vld[i] = 1
                        break

                dt_remain = r
                                    
                if dt_remain is None:
                    self._val[i] = d
                    self._vld[i] = 1 
                    break
                
#         for d, r in convgen(other, self.dtype, dt_remain):
#             self._val[pos] = d
#             pos += 1
#             if self._full():
#                 return r

        return dt_remain
   
    def _empty(self):
   
        for v in self._val:
            if (v is None) or getattr(v, '_empty', lambda : False)():
                return True
        else:
            return False    
           
#         return sum(self._vld) == 0
   
    @classmethod
    def _convto(cls, cls_other, val):
        try:
            TypeBase._convto(cls_other, val)
        except ConversionError:
            pass
        
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
    
    def _icon(self, other):
        
        for i, u in reversed(list(enumerate(self._vld))):
            if u:
                last_unset = i + 1
                break
        else:
            last_unset = 0
            
        if last_unset >= len(self):
            return (None, other)
        
        remain = other
        val = self._val.copy()
        
        while last_unset < len(self):
            try:
                dt_remain = self._val[last_unset]
                conv_gen = list(self.dtype.items())[last_unset][1]._convgen(remain, dt_remain)
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

    @classmethod
    def _to_tuple(cls, val):
        dout = []
        for val,vld in zip(val._val, val._vld):
            if not vld:
                break
            
            dout.append(val)

        return tuple(dout)

    @classmethod
    def _from_tuple(cls, other):
        dout = cls()
        for i, (item, dtype) in enumerate(zip(other, cls.dtype.values())):
            dout._val[i] = conv(item, dtype)
            dout._vld[i] = 1
            
        return dout
                
    def __eq__(self, other):
        other = convlist(other, self.__class__)
        if len(other) != 1:
            return False

        return (self._val == other[0]._val) and (self._vld == other[0]._vld)
    