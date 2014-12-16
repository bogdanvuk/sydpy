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

"""Module implements Bit aspect and bit data class."""

__bit_classes = {}

def Bit(w):
    if w not in __bit_classes:
        cls_name = 'bit'
        
        if w != 1:
            cls_name += str(w)
             
        __bit_classes[w] = type(cls_name, (bit,), dict(w=w))
        
    return __bit_classes[w] 

class bit(object):
    __slots__ = ['w', 'val', 'invld']
    
    w = 1
    
    def __init__(self, val=None, invld=0):

        if val is None:
            self.val = 0
            self.invld = ((1 << self.w) - 1)
        else:
            try:
                if (self.w == val.w):
                    self.val = val.val
                    self.invld = val.invld
                    return
                else:
                    val = val.val
            except AttributeError:
                if isinstance(val, str):
                    if 'b' in val:
                        pos = val.find('b')
                        val = int(val, 2)
                    elif 'x' in val:    
                        pos = val.find('x')
                        val = int(val, 16)
                    else:
                        val = int(val)
            
            mask = ((1 << self.w) - 1)
            
            self.val = val & mask
            self.invld = invld & mask

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
            self_invld = self.invld
            self_invld |= ((1 << w_slice) - 1) << low
            return Bit(self.w)(self.val, self_invld)
        else:
            ival = int(val)
            invld = 0
            if hasattr(val, 'invld'):
                invld = val.invld
            
            self_mask = ((1 << w_slice) - 1) << low
            
            self_val = self.val & (~self_mask)
            self_invld = self.invld  & (~self_mask)
            
            self_val |= (ival << low) & self_mask
            self_invld |= (invld << low) & self_mask
    
            return Bit(self.w)(self_val, self_invld)
    
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
        invld = self.invld >> low
        
        return Bit(w_slice)(val, invld)
                  
    def bitstr(self):
        val = self.val
        invld = self.invld
        bitstr = ''
        for i in range(self.w):
            if invld & 1:
                bitstr += 'u'
            else:
                bitstr += str(val & 1)
                
            invld >>= 1
            val >>= 1
            
        return '0b' + bitstr[::-1]
    
    def __str__(self):
        val = self.val
        invld = self.invld
        hexstr = ''
        for i in range(-(int(-self.w//4))):
            if invld & 0xf:
                hexstr += 'u'
            else:
                hexstr += '{0:1x}'.format(val & 0xf)
                
            invld >>= 4
            val >>= 4
            
        return '0x' + hexstr[::-1]

    __repr__ = __str__
    
    def __int__(self):
        return self.val
    
    def __len__(self):
        return self.w
    
    def __bool__(self):
        if self.val:
            return True
        else:
            return False
    
    def __invert__(self):
        return self.__class__(~self.val, None, self.invld)
    
    def __concat__(self, other):
        if hasattr(other, 'w'):
            other_w = other.w
        else:
            other_w = self.bit_length()
            
        return Bit(self.w + other_w)((self.val << other.w) + other.val, (self.invld << other.w) + other.invld)
    
    concat = __concat__
    
    def __add__(self, other):
        if hasattr(other, 'w'):
            width = max(self.w, other.w)
        else:
            width = self.w
            
#         return BitBase(int(self) + int(other), width)
        return Bit(width)(int(self) + int(other))
    
    def __radd__(self, other):
        if hasattr(other, 'w'):
            width = max(self.w, other.w)
        else:
            width = other.bit_length()
            
        return Bit(width)(int(self) + int(other))
    
    def __eq__(self, other):
        try:
            return (self.val == other.val) and (self.invld == other.invld)
        except AttributeError:
            return False
        
    def __ne__(self, other):
        return not self.__eq__(other)
        

bit = Bit(1)
bit8 = Bit(8)
bit16 = Bit(16)
bit32 = Bit(32)
bit64 = Bit(64)



    

    