'''
Created on Dec 3, 2014

@author: bvukobratovic
'''


class array(object):
    
    dtype_def = None
    
    def __init__(self, *args, dtype=None):
        
        if dtype is None:
            dtype = self.dtype_def
        
        self.dtype = dtype
               
        if not args:
            self.elems = []
        else:
            for a in args:
                self.elems.append(self.dtype(a))

    def _replace(self, key, val):
        if isinstance( key, slice ) :
            high = max(key.start, key.stop)
            low = min(key.start, key.stop)
            
            for key in range(low, high + 1):
                self.elems[key] = self.dtype(val)
        elif isinstance( key, int ) :
            self.elems[key] = self.dtype(val)
        else:
            raise TypeError("Invalid argument type.")
    
    def _hdl_gen_ref(self, conv):
        s = conv._hdl_gen_ref(self.elems[0])

        if len(self.elems) > 1:
            s += ", "
            for e in self.elems[1:]:
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
            
        a = cls(*args)
        
        return a._hdl_gen_ref(conv)
    
    @classmethod
    def deref(self, key):
        if isinstance( key, slice ) :
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
        
        return BitBase(val, w_slice, invld)
                  
#     def __setitem__(self, key, val):
#         if isinstance( key, slice ) :
#             #Get the start, stop, and step from the slice
# #             return [self[ii] for ii in xrange(*key.indices(len(self)))]
#             pass
#         elif isinstance( key, int ) :
#             if key >= self.w:
#                 raise IndexError("The index (%d) is out of range.".format(key))
#             
#             i = int(key)
#             self_val = int(self)
#             if val == 1:
#                 self_val |= (1 << i)
#             elif val == 0:
#                 self_val &= ~(1 << i)
#             
#             return BitBase(self_val, self.w)
#         else:
#             raise TypeError("Invalid argument type.")

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
    
#         return ('x{0:0' + str(-(int(-self.w/4))) + 'x}').format(int(self))
    __repr__ = __str__
    
    def __int__(self):
        return self.val
    
    def __len__(self):
        return self.w
    
    def __mod__(self, other):
        if hasattr(other, 'w'):
            other_w = other.w
        else:
            other_w = self.bit_length()
            
        return BitBase((self.val << other.w) + other.val, self.w + other_w, (self.invld << other.w) + other.invld)
    
    def __rmod__(self, other):
        if hasattr(other, 'w'):
            other_w = other.w
        else:
            other_w = self.bit_length()
            
        return BitBase((other.val << other_w) + self.val, self.w + other_w, (other.invld << other_w) + self.invld)
    
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
            
        return BitBase(int(self) + int(other), width)
    
    def __eq__(self, other):
        try:
            return (self.val == other.val) and (self.invld == other.invld)
        except AttributeError:
            return False
        
    def __ne__(self, other):
        return not self.__eq__(other)
        


    

    