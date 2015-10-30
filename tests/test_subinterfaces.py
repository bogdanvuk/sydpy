import pytest

@pytest.fixture
def sydpy():
    import sydpy
    return sydpy

def test(sydpy):
    
    class ChangeListener(object):
        
        def __init__(self, intf):
            self.intf = intf
            self.intf._sig.e.changed.subscribe(self)
            self.data = 0
        
        def resolve(self, pool):
            byte1 = (self.data + 1) & 0xff
            nibble3 = (self.data & 0xff) - ((self.data & 0xf00) >> 8)
            nibble3_old = ((self.data & 0xf00) >> 8)
            nibble4 = nibble3_old + ((nibble3_old & 0x3) << 2) | (nibble3_old >> 2)
            bit16 = ((self.data >> 15) & 1) ^ 1
            bit17 = (bit16 << 1) & ((self.data >> 15) & 1)
            bit1918 = self.data & 0x3
            bit1918_old = ((self.data >> 18) & 0xf)
            nibble6 = (bit1918_old * 2) & 0x3
            nibble6_old = ((self.data >> 18) & 0x3)
            nibble7 = int(nibble6_old / 2)
            nibble8 = nibble6_old >> 1
            
            self.data = nibble8 << 28 | nibble7 << 24 | nibble6 << 20 | bit1918 << 18 | bit17 << 17 | bit16 << 16 | nibble4 << 12 | nibble3 << 8 | byte1
            assert (self.data == int(self.intf.read()))
            
#             print(self.intf.read())
    
    class Test(sydpy.Component):
        @sydpy.compinit
        def __init__(self, **kwargs):
            self.inst('ch_gen', sydpy.Channel) 
            self.ch_gen <<= self.inst('dout', sydpy.isig, dtype=sydpy.bit32, dflt=0)
            self.inst('p_gen', sydpy.Process, self.gen, [sydpy.Delay(1)])
            self.lstn = ChangeListener(self.dout)
            
        def gen(self):
            self.dout[7:0] <<= self.dout[7:0] + 1
            self.dout[11:8] <<= (self.dout[7:0] - self.dout[11:8])[3:0]
            self.dout[15:12] <<= self.dout[11:8] + self.dout[9:8] % self.dout[11:10]
            self.dout[16] <<= ~self.dout[15]
            self.dout[17] <<= self.dout[16] & self.dout[15]
            self.dout[19:18] <<= self.dout[1:0]
            self.dout[23:20] <<= self.dout[19:18] * 2
            self.dout[27:24] <<= self.dout[23:20] / 2
            self.dout[31:28] <<= self.dout[23:20] >> 1
    
    conf = [
        ('sim'              , sydpy.Simulator),
        ('sim.top'          , Test),
        ('sim.duration'     , 512)
        ]

    sydpy.system.set_config(conf)
    sydpy.system.sim.run()

    assert 0
