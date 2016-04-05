import pytest
from sydpy import *
from sydpy.extens.profiler import Profiler

@pytest.fixture
def system():
    restart_sydsys()
    return sydsys()

def test_convgen(system):

    gen_period = 2
    max_cycles = 5
    array_size = 100
    
    class ChangeListener(object):

        def __init__(self, intf, system):
            self.intf = intf
            self.intf.e.changed.subscribe(self)
            self.last_time = 0
            self.system = system
            self.data = 0

        def resolve(self, pool):
            time = self.system.sim.time
            if self.data == array_size:
                self.data = 0
                assert time == self.last_time + gen_period
            assert self.data == int(self.intf.read())
            self.data += 1
#             print(self.intf.read())
            self.last_time = time

    class Test(Component):
        @compinit
        def __init__(self, **kwargs):
            self.inst('dout', Isig, dtype=bit8) << \
                self.inst('gen', Isig, dtype=Array(bit8)) 
            
            self.inst('p_gen', Process, self.p_gen, [Delay(gen_period)])
            self.inst('p_sink', Process, self.p_sink, [])
            self.lstn = ChangeListener(self.dout, system)

        def p_gen(self):
            self.gen.bpush(list(range(array_size)))

        def p_sink(self):
            while(1):
#                 print(self.dout.bpop())
                self.dout.bpop()

        def pclk(self):
            self.dout.clk <<= ~self.dout.clk

    conf = [
        ('sim'              , Simulator),
        ('top'              , Test),
        ('sim.duration'     , gen_period * max_cycles)
        ]

    system.set_config(conf)
    system.sim.run()
