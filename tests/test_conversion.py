from sydpy.types._type_base import convgen, convlist
from sydpy.types.bit import bit8, bit, Bit, bit32, bit16
from sydpy.types.array import Array
from sydpy.types.struct import Struct

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
    assert convlist(bit8(0xaa), bit) == [0x0, 0x1, 0x0, 0x1, 0x0, 0x1, 0x0, 0x1]
    assert convlist(bit8(0xaa), Bit(9)) == [Bit(9)(0xaa, 0xff)]
    assert convlist(bit8(0xaa), Bit(5)) == [0x0a, Bit(5)(0x5, 0x7)]
    assert convlist(bit32(0xdeadbeaf), Bit(4)) == [0x0f, 0x0a, 0x0e, 0x0b, 0x0d, 0x0a, 0x0e, 0x0d]

def test_bit_to_array():
    assert convlist(bit32(0xdeadbeaf), Array(Bit(4))) == [[0xf,0xa,0xe,0xb,0xd,0xa,0xe,0xd]]
    assert convlist(bit32(0xdeadbeaf), Array(Bit(5))) == [[0x0f,0x15,0x0f,0x1b,0x0a,0x0f,Bit(5)(0x3, 0x3)]]

def test_array_to_bit():
    assert convlist(Array(Bit(4))([0xf,0xa,0xe,0xb,0xd,0xa,0xe,0xd]), bit32) == [0xdeadbeaf]
    assert convlist(Array(Bit(4))([0xf,0xa,0xe,0xb,0xd,0xa,0xe,0xd]), bit8) == [0xaf, 0xbe, 0xad, 0xde]
    assert convlist(Array(Bit(5))([0xf,0xa,0xe,0xb,0xd,0xa,0xe,0xd]), Bit(7)) == [0x4f, 0x72, 0x56, 0x26, 0x39, Bit(7)(0xd, 0x1f)]

def test_array_to_array():
    assert convlist(Array(Bit(4))([0xf,0xa,0xe,0xb,0xd,0xa,0xe,0xd]), Array(bit8)) == [Array(bit8)([0xaf, 0xbe, 0xad, 0xde])]

def test_bit_to_struct():
    assert convlist(bit16(0xabcd), Struct(('f1', bit8), ('f2', bit8))) == [(0xcd,0xab)]
    assert convlist(bit16(0xabcd), Struct(('f1', Bit(3)), ('f2', Bit(13)))) == [(0x5,0x1579)]
    assert convlist(bit16(0xabcd), Struct(('f1', Bit(3)), ('f2', Bit(5)), ('f3', Bit(7)))) == [(0x5,0x19,0x2b), (Bit(3)(0x1, 0x1), Bit(5)(), Bit(7)())]
#    print(convlist(bit16(0xabcd), Struct(('f1', Bit(3)), ('f2', Bit(5)), ('f3', Bit(7)))))

def test_struct_to_bit():
    assert convlist(Struct(('f1', bit8), ('f2', bit8))((0xcd, 0xab)), bit16) == [0xabcd]
    
    print(convlist(Struct(('f1', bit8), ('f2', bit8))((0xcd, 0xab)), bit16))
    #assert convlist(bit16(0xabcd), Struct(('f1', bit8), ('f2', bit8))) == [(0xcd,0xab)]

# test_bit_to_bit()
# test_bit_to_array()
# test_array_to_bit()
# test_array_to_array()
# test_bit_to_struct()
test_struct_to_bit()
