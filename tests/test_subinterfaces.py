import pytest

@pytest.fixture
def sydpy():
    import sydpy
    return sydpy

def test(sydpy):
    
    class ChangeListener(object):
        
        def __init__(self, intf):
            self.intf = intf
            self.intf.e.changed.subscribe(self)
            self.data = 0
        
        def data_slice(self, key):
            if isinstance( key, slice ) :
                high = max(key.start, key.stop)
                low = min(key.start, key.stop)
            elif isinstance( key, int ) :
                high = low = int(key)
                
            w_slice = high - low + 1
                
            return (self.data >> low) & ((1 << w_slice) - 1)
        
        def resolve(self, pool):
            byte1 = (self.data + 1) & 0xff
            nibble3 = (self.data_slice(slice(7,0)) - self.data_slice(slice(11,8))) & 0xf
            nibble4 = (self.data_slice(slice(11,8)) + ((self.data_slice(slice(9,8)) << 2) | (self.data_slice(slice(11,10))))) & 0xf
            bit16 = self.data_slice(15) ^ 1
            bit17 = self.data_slice(16) & self.data_slice(15)
            bit1918 = self.data_slice(slice(1,0))
            nibble6 = (self.data_slice(slice(19,18)) * 2) & 0x3
            nibble7 = (int(self.data_slice(slice(23,20)) / 2)) & 0xf
            nibble8 = (self.data_slice(slice(23,20)) >> 1) & 0xf

            self.data = nibble8 << 28 | nibble7 << 24 | nibble6 << 20 | bit1918 << 18 | bit17 << 17 | bit16 << 16 | nibble4 << 12 | nibble3 << 8 | byte1
            assert (self.data == int(self.intf.read()))
            
#             print(self.intf.read())
    
    class Test(sydpy.Component):
        @sydpy.compinit
        def __init__(self, **kwargs):
            self.inst('ch_gen', sydpy.Channel) 
            self.ch_gen <<= self.inst('dout', sydpy.Isig, dtype=sydpy.bit32, dflt=0)
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
#             print(self.dout.read(), self.dout[16].read(), self.dout[15].read())
    conf = [
        ('sim'              , sydpy.Simulator),
        ('top'              , Test),
        ('sim.duration'     , 512)
        ]

    sydpy.system.set_config(conf)
    sydpy.system.sim.run()
