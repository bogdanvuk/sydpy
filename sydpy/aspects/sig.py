
from copy import copy
from sydpy._process import always

def _sig_to_seq_arch(self, clk, data_i, data_o):
    @always(self, clk.e.posedge)
    def proc():
        data_o.next = data_i

class sig(object):
    
    def __seq__(self, val):
        return _sig_to_seq_arch
    
    def __str__(self):
        if self.dtype is not None:
            try:
                name = self.dtype.__name__
            except AttributeError:
                name = str(self.dtype)
        else:
            name = 'sig'

        return name
    
    def _hdl_gen_decl(self):
        if self.dtype is not None:
            return self.dtype._hdl_gen_decl()
        else:
            return ''
    
    def deref(self, key):
        asp_copy = copy(self)
        asp_copy.dtype = self.dtype.deref(key)
        
        return asp_copy
    
    __repr__ = __str__
        
    def __call__(self, *args):
        if args:
            try:
                return self.dtype(args[0])
            except TypeError:
                return args[0]
        else:
            try:
                return self.dtype()
            except TypeError:
                return None
    
    def __init__(self, dtype=None):
        self.dtype = dtype