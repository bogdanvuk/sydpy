from sydpy.types._type_base import convgen, convlist
from sydpy.types.bit import bit8, bit, Bit, bit32
from sydpy.types.array import Array

def convert(din, dout):
    while (din is not None) and (not din._empty()):
        din = dout._iconcat(din)
        if dout._full():
            yield dout
            dout = dout.__class__()
            
    if not dout._empty():
        yield dout


# def convert(din, dout):
#     return dout._iconcat(din)

def test_bit_to_bit():
    assert convlist(bit, bit8(0xaa)) == [0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1]
    assert convlist(Bit(9), bit8(0xaa)) == [Bit(9)(0xaa, 0xff)]
    assert convlist(Bit(5), bit8(0xaa)) == [0x0a, Bit(5)(0x5, 0x7)]
    assert convlist(Bit(4), bit32(0xdeadbeaf)) == [0x0f, 0x0a, 0x0e, 0x0b, 0x0d, 0x0a, 0x0e, 0x0d]

def test_bit_to_array():
    assert convlist(Array(Bit(4)), bit32(0xdeadbeaf)) == [[0xf,0xa,0xe,0xb,0xd,0xa,0xe,0xd]]
    assert convlist(Array(Bit(5)), bit32(0xdeadbeaf)) == [[0x0f,0x15,0x0f,0x1b,0x0a,0x0f,Bit(5)(0x3, 0x3)]]

test_bit_to_bit()
test_bit_to_array()
