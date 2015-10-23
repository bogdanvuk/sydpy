from sydpy.configurator import Configurator
from sydpy.component import Component
from sydpy.sydpy import Sydpy
from sydpy.unit import Unit
from sydpy.channel import Channel
from sydpy.intfs.isig import isig
from sydpy.types import bit8
from sydpy._delay import Delay
from sydpy.module import proc, Module
from sydpy.process import Process

class Generator(Module):
    
    def build(self):
        self.chout <<= isig(self, "sout", dtype=bit8, dflt=0)
        Process(self, self.gen, [Delay(20)])
        
    def gen(self):
        self.sout <<= self.sout + 1
    
class Sink(Module):
    def build(self):
        self.chin >>= isig(self, "sin", dtype=bit8, dflt=0)
        Process(self, self.psink)

    def psink(self):
        print(self.find('/sim').time, ': ', self.sin)
    
class TestDff(Module):
    def build (self):
        Channel(self, 'ch_gen')
        self.gen = Generator()
        Generator(self, 'ch_gen').conf(chout=self.ch_gen, dtype=bit8)
        
        self.gen = Generator(chout=self.ch_gen)
        Generator(self, 'gen', chout=self.ch_gen)
        Sink(self, 'sink', chin=self.ch_gen)

conf = {
        '/cfg.units'        : ['sydpy.simulator.Simulator', 'sydpy.server.Server'],
        '/sim.top'          : TestDff,
        '/sim.duration'     : 100
        }

sydpy = Sydpy(conf)
sydpy.sim.run()

print(sydpy.index())
