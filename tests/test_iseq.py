import pytest

@pytest.fixture
def sydpy():
    import sydpy
    return sydpy

def test_single(sydpy):
     
    clk_period = 10
    gen_period = 2
 
    class ChangeListener(object):
     
        def __init__(self, intf, system):
            self.intf = intf
            self.intf.e.changed.subscribe(self)
            self.last_time = 0
            self.system = system
         
        def resolve(self, pool):
            time = self.system.sim.time
            if self.last_time > 0:
                assert (time - self.last_time) == max(gen_period, clk_period)
                assert (time // gen_period) == int(self.intf.read())
                 
            print(self.intf.read())
            self.last_time = time
     
    class Test(sydpy.Component):
        @sydpy.compinit
        def __init__(self, **kwargs):
            self.inst('dout', sydpy.iseq, dtype=sydpy.bit8, dflt=0) 
            self.inst('pclk', sydpy.Process, self.pclk, [sydpy.Delay(clk_period // 2)])
            self.inst('p_gen', sydpy.Process, self.gen, [sydpy.Delay(gen_period)])
            self.lstn = ChangeListener(self.dout, sydpy.system)
             
        def gen(self):
            self.dout.data <<= self.dout.data + 1
             
        def pclk(self):
            self.dout.clk <<= ~self.dout.clk
 
    conf = [
        ('sim'              , sydpy.Simulator),
        ('top'              , Test),
        ('sim.duration'     , 512)
        ]
 
    sydpy.system.set_config(conf)
    sydpy.system.sim.run()
      
def test_iseq2isig(sydpy):

    clk_period = 8
    gen_period = 2
    
    class ChangeListener(object):
    
        def __init__(self, intf, system):
            self.intf = intf
            self.intf.e.changed.subscribe(self)
            self.last_time = 0
            self.system = system
        
        def resolve(self, pool):
            time = self.system.sim.time
            if self.last_time > 0:
                assert (time - self.last_time) == max(gen_period, clk_period // 2)
                assert (time // gen_period) == int(self.intf.read())
                
            print(self.intf.read())
            self.last_time = time
     
    class Test(sydpy.Component):
        @sydpy.compinit
        def __init__(self, **kwargs):
            self.inst('ch_gen', sydpy.Channel) 
            self.ch_gen <<= self.inst('din', sydpy.iseq, dtype=sydpy.bit8, dflt=0)
            self.ch_gen >>= self.inst('dout', sydpy.isig, dtype=sydpy.bit8, dflt=0) 
            self.inst('pclk', sydpy.Process, self.pclk, [sydpy.Delay(clk_period // 4)])
            self.inst('p_gen', sydpy.Process, self.gen, [sydpy.Delay(gen_period)])
            self.lstn = ChangeListener(self.dout, sydpy.system)
            
        def gen(self):
            self.din.valid <<= (int(self.din.data) % 2 == 0)
            self.din <<= self.din
    #         print(self.din.valid.read_next())
    #         print(self.din.data.read_next())
            
        def pclk(self):
            self.din.clk <<= ~self.din.clk
    
    conf = [
        ('sim'              , sydpy.Simulator),
        ('top'              , Test),
        ('sim.duration'     , 512)
        ]
    
    sydpy.system.set_config(conf)
    sydpy.system.sim.run()

def test_isig2iseq(sydpy):

    clk_period = 8
    gen_period = 2
    
    class ChangeListener(object):
    
        def __init__(self, intf, system):
            self.intf = intf
            self.intf.e.changed.subscribe(self)
            self.last_time = 0
            self.system = system
        
        def resolve(self, pool):
            time = self.system.sim.time
            if self.last_time > 0:
                assert (time - self.last_time) == max(gen_period, clk_period)
                assert (time // gen_period) == int(self.intf.read())
                 
            self.last_time = time
     
    class Test(sydpy.Component):
        @sydpy.compinit
        def __init__(self, **kwargs):
            self.inst('ch_gen', sydpy.Channel) 
            self.ch_gen <<= self.inst('din', sydpy.isig, dtype=sydpy.bit8, dflt=0)
            self.ch_gen >>= self.inst('dout', sydpy.iseq, dtype=sydpy.bit8, dflt=0) 
            self.inst('pclk', sydpy.Process, self.pclk, [sydpy.Delay(clk_period // 4)])
            self.inst('p_gen', sydpy.Process, self.gen, [sydpy.Delay(gen_period)])
            self.inst('pready', sydpy.Process, self.pready, [self.dout.clk.e.posedge])
            self.lstn = ChangeListener(self.dout, sydpy.system)
            
        def gen(self):
            self.din <<= self.din + 1
            
        def pclk(self):
            self.dout.clk <<= ~self.dout.clk
            
        def pready(self):
            self.dout.ready <<= ~self.dout.ready
    
    conf = [
        ('sim'              , sydpy.Simulator),
        ('top'              , Test),
        ('sim.duration'     , 512)
        ]
    
    sydpy.system.set_config(conf)
    sydpy.system.sim.run()

