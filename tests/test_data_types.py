'''
Created on Dec 25, 2014

@author: bvukobratovic
'''
from sydpy import Bit, Vector
from random import randint 

def test_bit():
    # Test Bit initialization and conversion to hex
#     size = randint(0, 1024)
    size = 16
    val = randint(0, (1<<size)*10)
    b_val = Bit(size)(val)
    assert int(str(b_val), 16) == val & ((1 << size) - 1)
    
    # Test slicing and deref type
    high = randint(0, size - 1)
    low = randint(0, high)
    slice_w = high - low + 1
    slice_val = b_val[low:high]
    slice_mask = ((1 << slice_w) - 1)
    assert int(slice_val) == (val >> low) & slice_mask
    
    assert b_val.deref(slice(low, high)).w == slice_w
    
    replace_val = randint(0, slice_mask)
    b_repl_val = b_val._replace(slice(low, high), replace_val)
    mask = ((1 << size) - 1) ^ (slice_mask << low)
    assert int(b_repl_val) == ((val & mask) | ((replace_val & slice_mask) << low))
    
    size2 = 16
    val2 = randint(0, (1<<size)*10)
    b_val2 = Bit(size)(val2)
    assert int(b_val.__concat__(b_val2)) == (((val & ((1 << size) - 1)) << size2) | (val2 & ((1 << size2) - 1)))
    
def test_vector():
    pass
