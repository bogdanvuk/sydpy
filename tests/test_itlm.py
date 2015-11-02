import pytest

@pytest.fixture
def sydpy():
    import sydpy
    return sydpy

def test_itlm2isig(sydpy):

    clk_period = 8
    gen_period = 2
    
    class ChangeListener(object):
    
        def __init__(self, intf, system):
            self.intf = intf
            self.intf.e.changed.subscribe(self)
            self.last_time = 0
            self.delta_count = 0
            self.system = system
        
        def resolve(self, pool):
            self.delta_count += 1
            time = self.system.sim.time
            if self.last_time > 0:
                if self.delta_count < 5:
                    assert time == self.last_time
                else:
                    assert (time - self.last_time) == gen_period
                    self.delta_count = 1 
                
                assert (4*(time // gen_period - 1)  + self.delta_count) == int(self.intf.read())
            
            print(self.intf.read())
            self.last_time = time
     
    class Test(sydpy.Component):
        @sydpy.compinit
        def __init__(self, **kwargs):
            self.inst('dout', sydpy.isig, dtype=sydpy.bit8) << \
                self.inst('din', sydpy.itlm , dtype=sydpy.bit8)
            
            self.inst('p_gen', sydpy.Process, self.gen, [sydpy.Delay(gen_period)])
            self.lstn = ChangeListener(self.dout, sydpy.system)
            
        def gen(self):
            for i in range(self.din + 1, self.din + 5):
                print('tlm_gen: ', i)
                self.din <<= i 
    
    conf = [
        ('sim'              , sydpy.Simulator),
        ('top'              , Test),
        ('sim.duration'     , 512)
        ]
    
    sydpy.system.set_config(conf)
    sydpy.system.sim.run()
