from copy import copy
from sydpy._process import always

def _sig_to_seq_arch(self, clk, data_i, data_o):
    @always(self, clk.e.posedge)
    def proc():
        data_o.next = data_i

class seq(object):
    
    def __init__(self, dtype=None, clk=None):
        self.dtype = dtype
        self.clk = clk

    def _to_sig(self, val):
        pass
    
    def _from_sig(self, val):
        yield _sig_to_seq_arch
        
    def conv_path(self, val):
        try:
            yield from getattr(self, '_from_' + val.__class__.__name__)(val)
        except AttributeError:
            yield from getattr(val, '_to_' + self.__class__.__name__)(self)
    
    def __str__(self):
        name = 'seq_'
        
        if self.dtype is not None:
            try:
                name += self.dtype.__name__
            except AttributeError:
                name += str(self.dtype)
            
#         if self.clk is not None:
#             name += ',' + str(self.clk) 

        return name
    
    __repr__ = __str__
    
    def _hdl_gen_decl(self):
        if self.dtype is not None:
            return self.dtype._hdl_gen_decl()
        else:
            return ''
    
    def deref(self, key):
        asp_copy = copy(self)
        asp_copy.dtype = self.dtype.deref(key)
        
        return asp_copy
        
    def __call__(self, *args):
        if args:
            return self.dtype(args[0])
        else:
            return self.dtype()


