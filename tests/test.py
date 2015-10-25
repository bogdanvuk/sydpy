from sydpy.configurator import Configurator
from sydpy.component import Component, system, compinit
from sydpy.unit import Unit
from sydpy.channel import Channel
from sydpy.intfs.isig import isig
from sydpy.types import bit8, bit
from sydpy._delay import Delay
from sydpy.module import proc, Module
from sydpy.process import Process
from sydpy.simulator import Simulator

class Generator(Module):
    
    @compinit 
    def __init__(self, name, chout, dtype=bit):
        chout <<= self.inst('sout', isig, dtype=dtype, dflt=0)
        self.proc('gen', [Delay(20)])

    def gen(self):
        self.sout <<= self.sout + 1
     
class Sink(Module):
    @compinit
    def __init__(self, name, chin):
        chin >>= self.inst('sin', isig, dtype=bit8, dflt=0)
        self.proc('psink')

    def psink(self):
        print(system['sim'].time, ': ', self.sin)
     
class TestDff(Module):
    @compinit
    def __init__ (self, name):
        self.inst('ch_gen', Channel)
        self.inst('gen', Generator, chout=self.ch_gen, dtype=bit8)
        self.inst('sink', Sink, chin=self.ch_gen)

conf = [
        ('sim'              , Simulator),
        ('sim.top'          , TestDff),
        ('sim.duration'     , 100)
        ]

system.set_config(conf)
system.sim.run()
