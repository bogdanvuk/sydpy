from sydpy.configurator import Configurator
from sydpy.component import Component
from sydpy.sydpy import Sydpy
from sydpy.unit import Unit
from sydpy.channel import Channel
from sydpy.intfs.isig import isig
from sydpy.types import bit8

class Generator(Unit):
    def build(self):
        self.chout.drive(isig(self, "sout", dtype=bit8, dflt=0))
        
class Source(Unit):
    def build(self):
        self.chin.sink(isig(self, "sin", dtype=bit8, dflt=0))    
    
class TestDff(Unit):
    def build (self):
        Channel(self, 'ch_gen')
        
        Generator(self, 'gen', chout=self.ch_gen)
        Source(self, 'src', chin=self.ch_gen)

conf = {
        '/cfg.units'        : ['sydpy.simulator.Simulator'],
        '/sim.top'           : TestDff,
        }

sydpy = Sydpy(conf)
sydpy.sim.run()

print(sydpy.index())
