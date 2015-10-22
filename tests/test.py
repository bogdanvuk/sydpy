from sydpy.configurator import Configurator
from sydpy.component import Component
from sydpy.sydpy import Sydpy
from sydpy.unit import Unit
from sydpy.channel import Channel
from sydpy.intfs.isig import isig
from sydpy.types import bit8
from sydpy._delay import Delay
from sydpy.module import proc, Module

class Generator(Module):
    def build(self):
        self.chout.drive(isig(self, "sout", dtype=bit8, dflt=0))

    @proc
    def gen(self):
        val = 0
        while(1):
            val += 1
            self.sout.write(val)
            self.sim.wait(Delay(20))
    
class Sink(Module):
    def build(self):
        self.chin.sink(isig(self, "sin", dtype=bit8, dflt=0))
        
    @proc
    def psink(self):
        print(self.find('/sim').time, ': ', self.sin.read())
    
class TestDff(Module):
    def build (self):
        Channel(self, 'ch_gen')
        
        Generator(self, 'gen', chout=self.ch_gen)
        Sink(self, 'sink', chin=self.ch_gen)

conf = {
        '/cfg.units'        : ['sydpy.simulator.Simulator'],
        '/sim.top'          : TestDff,
        '/sim.duration'     : 100
        }

sydpy = Sydpy(conf)
sydpy.sim.run()

print(sydpy.index())
