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

"""Module implements Bit data type generator and bit data type."""

__bit_classes = {}

from ._type_base import TypeBase
from sydpy import ConversionError

def Bit(w):
    if w not in __bit_classes:
        cls_name = 'bit'
        
#         if w != 1:
#             cls_name += str(w)
             
        __bit_classes[w] = type(cls_name, (bit,), dict(w=w))
        
    return __bit_classes[w] 

def bit_normalization(self, other):
    self_val = self.val
    
    try:
        other_val = other.val
        
        if other.w < self.w:
            dif_mask = ((1 << (self.w - other.w)) - 1) << other.w
            other_vld = dif_mask | other.vld
            
            self_vld = self.vld
            width = self.w
        else:
            dif_mask = ((1 << (other.w - self.w)) - 1) << self.w
            self_vld = dif_mask | self.vld
            other_vld = other.vld
            width = other.w 
    except AttributeError:
        other_vld = self._mask
        other_val = other
        self_vld = self.vld
        width = self.w

    return width, self_val, self_vld, other_val, other_vld 

class bit(TypeBase):
    __slots__ = ['val', 'vld']
    
    w = 1
    
    def __init__(self, val=None, vld=None):

        self._mask = ((1 << self.w) - 1)
        
        if vld is None:
            vld = self._mask

        if val is None:
            self.val = 0
            self.vld = 0
        else:
            try:
                vld = val.vld
                val = val.val
            except AttributeError:
                if isinstance(val, str):
                    if 'b' in val:
                        pos = val.find('b')
                        vld = (1 << (len(val) - pos)) - 1
                        val = int(val, 2)
                    elif 'x' in val:    
                        pos = val.find('x')
                        vld = (1 << ((len(val) - pos)*4)) - 1
                        val = int(val, 16)
                    else:
                        val = int(val)
            
            self.val = val & self._mask
            self.vld = vld & self._mask

    def _replace(self, key, val):
        if isinstance( key, slice ) :
            #Get the start, stop, and step from the slice
#             return [self[ii] for ii in xrange(*key.indices(len(self)))]
            high = max(key.start, key.stop)
            low = min(key.start, key.stop)
            
        elif isinstance( key, int ) :
            high = low = int(key)
        else:
            raise TypeError("Invalid argument type.")

        w_slice = high - low + 1
        
        if high >= self.w:
            raise IndexError("The index ({0}) is out of range.".format(key))
        
        if hasattr(val, 'w'):
            if val.w > w_slice:
                raise IndexError("The applied value width ({0}) is larger than the slice size ({1}).".format(val.w, w_slice))
        
        if val is None:
            self_vld = self.vld
            self_vld |= ((1 << w_slice) - 1) << low
            return Bit(self.w)(self.val, self_vld)
        else:
            ival = int(val) & ((1 << w_slice) - 1)
            
            if hasattr(val, 'vld'):
                vld = val.vld
            else:
                vld = self.vld
            
            self_mask = self._mask ^ (((1 << w_slice) - 1) << low)
            
#             print("BV:")
#             print('ival: ', hex(ival))
#             print('self_mask: ', hex(self_mask))
            
            self_val = (self.val & self_mask) | (ival << low)
            self_vld = (self.vld & self_mask) | (vld << low)
            
#             print('self_val: ', hex(self_val))
            
            return Bit(self.w)(self_val, self_vld)
    
    def _hdl_gen_ref(self, conv):
        if self.w < 4:
            s = self.bitstr()
            s = s.replace('0b', "{0}'b".format(self.w)).replace('u', 'x')
        else:
            s = self.__repr__()
            s = s.replace('0x', "{0}'h".format(self.w)).replace('u', 'x')
            
        return s
    
    @classmethod
    def _hdl_gen_decl(cls):
        if cls.w_def == 1:
            return ''
        else:
            return '[{0}:0]'.format(cls.w_def) 
        
    @classmethod
    def _hdl_gen_call(cls, conv=None, node=None):
        args = []
        for a in node.args:
            args.append(conv.obj_by_node(a))
            
        a = cls(*args)
        
        return a._hdl_gen_ref(conv)
    
    @classmethod
    def deref(self, key):
        if isinstance( key, slice ) :
            #Get the start, stop, and step from the slice
#             return [self[ii] for ii in xrange(*key.indices(len(self)))]
            high = max(key.start, key.stop)
            low = min(key.start, key.stop)
            
        elif isinstance( key, int ) :
            high = low = int(key)
        else:
            raise TypeError("Invalid argument type.")
        
        width = high - low + 1
        return Bit(width)
    
    def __iter__(self):
        if self.w > 1:
            for i in range(self.w):
                yield self.__getitem__(i)
        else:
            raise TypeError
    
    @classmethod
    def _rnd(cls, rnd_gen):
        return cls(rnd_gen._rnd_int(0, (1 << cls.w) - 1))
        
    def __getitem__(self, key):
        if isinstance( key, slice ) :
            #Get the start, stop, and step from the slice
#             return [self[ii] for ii in xrange(*key.indices(len(self)))]
            high = max(key.start, key.stop)
            low = min(key.start, key.stop)
            
        elif isinstance( key, int ) :
            high = low = int(key)
        else:
            raise TypeError("Invalid argument type.")

        w_slice = high - low + 1
        
        if high >= self.w:
            raise IndexError("The index ({0}) is out of range.".format(key))
        
        val = self.val >> low
        vld = self.vld >> low
        
        return Bit(w_slice)(val, vld)
                  
    def bitstr(self):
        val = self.val
        vld = self.vld
        bitstr = ''
        for i in range(self.w):
            if vld & 1:
                bitstr += str(val & 1)
            else:
                bitstr += 'U'
                
            vld >>= 1
            val >>= 1
            
        return '0b' + bitstr[::-1]
    
    def __str__(self):
        val = self.val
        vld = self.vld
        hexstr = ''
        for i in range(-(int(-self.w//4))):
            if vld & 0xf:
                hexstr += '{0:1x}'.format(int(val & 0xf))
            else:
                if (vld & 0xf) == 0:
                    hexstr += 'U'
                else:
                    hexstr += 'u'
            vld >>= 4
            val >>= 4
            
        return '0x' + hexstr[::-1]

    __repr__ = __str__
    
    def __len__(self):
        return self.w
    
    def _full(self):
        if self.vld == self._mask:
            return True
        else:
            return False
        
    def _icon(self, other):
        try:
            for last_unset in reversed(range(self.w)):
                if (self.vld & (1 << last_unset)):
                    last_unset += 1
                    break
            else:
                last_unset = 0
    
            space_left = self.w - last_unset
            
            oth_val = other.val & ((1 << space_left) - 1)
            oth_vld = other.vld & ((1 << space_left) - 1)
            
            if other.w > space_left:
            
                oth_left_val = other.val >> space_left
                oth_left_vld = other.vld >> space_left
                
                new_other = Bit(other.w - space_left)(oth_left_val, oth_left_vld)
        
            else:
                new_other = None
    
            vld_mask = (1 << last_unset) - 1
            
            new_self = Bit(self.w)((oth_val << last_unset) | (vld_mask & self.val), (oth_vld << last_unset) | self.vld)
    
            return (new_self, new_other)
        
        except:
            raise ConversionError
    
    def __concat__(self, other):
        if hasattr(other, 'w'):
            other_w = other.w
        else:
            other_w = self.bit_length()
            
        return Bit(self.w + other_w)((self.val << other.w) + other.val, (self.vld << other.w) + other.vld)
    
    concat = __concat__
    __mod__ = __concat__
    
    @classmethod
    def _from_bit(cls, other):
        if cls.w == other.w:
            return other
        else:
            raise ConversionError
    
    @classmethod    
    def _from_int(cls, other):
        return cls(other)
    
    
#     def __nonzero__(self):
#         if self.read():
#             return 1
#         else:
#             return 0
 
    def __bool__(self):    
        return bool(self.val)
        
    # integer-like methods

    def __add__(self, other):
        try:
            other_val = other.val
            width = max(self.w, other.w)
            if (not other._full) or (not self._full):
                return Bit(width)()
            
        except AttributeError:
            other_val = other
            width = self.w

        return Bit(width)(other_val + self.val)
        
    def __radd__(self, other):
        return self.__add__(other)
    
#     def __sub__(self, other):
#         try:
#             val = other.read()
#         except AttributeError:
#             val = other
#         
#         return self.read() - val
#     def __rsub__(self, other):
#         return other - self.read()
# 
#     def __mul__(self, other):
#         try:
#             other = other.read()
#         except AttributeError:
#             pass
#         
#         return self.read() * other
#     def __rmul__(self, other):
#         return other * self.read()
# 
#     def __div__(self, other):
#         try:
#             other = other.read()
#         except AttributeError:
#             pass
#         
#         return self.read() / other
#     def __rdiv__(self, other):
#         return other / self.read()
#     
#     def __truediv__(self, other):
#         try:
#             other = other.read()
#         except AttributeError:
#             pass
#         
#         return self.read().__truediv__(other)
#     
#     def __rtruediv__(self, other):
#         return other.__truediv__(self.read())
#     
#     def __floordiv__(self, other):
#         try:
#             other = other.read()
#         except AttributeError:
#             pass
#         
#         return self.read() // other
#     def __rfloordiv__(self, other):
#         return other //  self.read()
#     
#     def __mod__(self, other):
#         try:
#             other = other.read()
#         except AttributeError:
#             pass
#         
#         return self.read() % other
#     def __rmod__(self, other):
#         return other % self.read()
# 
#     # XXX divmod
#     
#     def __pow__(self, other):
#         try:
#             other = other.read()
#         except AttributeError:
#             pass
#         
#         return self.read() ** other
#     def __rpow__(self, other):
#         return other ** self.read()

    def __rshift__(self, other):
        vld_mask = ((1 << other) - 1) << (self.w - other)
        
        return self.__class__(self.val >> other, ((self.vld >> other) | vld_mask))
    
    def __lshift__(self, other):
        vld_mask = ((1 << other) - 1)
        
        return self.__class__(self.val << other, ((self.vld << other) | (vld_mask)))
    
    def __xor__(self, other):
        width, self_val, self_vld, other_val, other_vld  = bit_normalization(self, other)
        
        return Bit(width)(self_val ^ other_val, self_vld & other_vld)
    
    def __rxor__(self, other):
        return other ^ self.val

#     def __rlshift__(self, other):
#         return other << self.read()
            
#     def __rrshift__(self, other):
#         return other >> self.read()
           
    def __and__(self, other):
        width, self_val, self_vld, other_val, other_vld  = bit_normalization(self, other)
        
        return Bit(width)(self_val & other_val, self_vld & other_vld)

    
    def __rand__(self, other):
        return other & self.read()

    def __or__(self, other):
        try:
            other = other.read()
        except AttributeError:
            pass
        return self.read() | other
    def __ror__(self, other):
        return other | self.read()
    
    def __neg__(self):
        return -self.read()

    def __pos__(self):
        return +self.read()

    def __abs__(self):
        return abs(self.read())

    def __invert__(self):
        return self.__class__(~self.val, self.vld)
            
    # conversions
    
    def __int__(self):
        return self.val
        
    def __float__(self):
        return float(self.read())
    
    def __oct__(self):
        return oct(self.read())
    
    def __hex__(self):
        return hex(self.read())
    
    def __index__(self):
        return int(self)


    # comparisons
    def __eq__(self, other):
        try:
            return (self.val == other.val) and (self.vld == other.vld)
        except AttributeError:
            try:
                return (self.val == int(other)) and (self.vld == self._mask)
            except TypeError:
                return False
     
    def __ne__(self, other):
        return not self.__eq__(other)
     
    def __lt__(self, other):
        return self.val < other
    def __le__(self, other):
        return self.val <= other
    def __gt__(self, other):
        return self.val > other
    def __ge__(self, other):
        return self.val >= other

bit = Bit(1)
bit8 = Bit(8)
bit16 = Bit(16)
bit32 = Bit(32)
bit64 = Bit(64)



    

    