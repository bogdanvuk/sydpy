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
from sydpy.cosim import Cosim
from sydpy.xsim import XsimIntf
from sydpy.server import Server

class Generator(Component):
    
    @compinit 
    def __init__(self, chout, dtype=bit, **kwargs):
        chout <<= self.inst('sout', isig, dtype=dtype, dflt=0)
        self.inst('p_gen', Process, self.gen, [Delay(20)])

    def gen(self):
        self.sout <<= self.sout + 1
     
class Sink(Cosim):
    @compinit
    def __init__(self, chin, chout, **kwargs):
        chin >>= self.inst('din', isig, dtype=bit8, dflt=0)
        chout <<= self.inst('dout', isig, dtype=bit8, dflt=0)
     
class TestDff(Module):
    @compinit
    def __init__ (self, name):
        for ch in ['ch_gen', 'ch_out']:
            self.inst(ch, Channel)
            
        self.inst('gen', Generator, chout=self.ch_gen, dtype=bit8)
        self.inst('sink', Sink, chin=self.ch_gen, chout=self.ch_out)

conf = [
        ('sim'              , Simulator),
        ('xsim'             , XsimIntf),
        ('server'           , Server),
        ('xsim.builddir'    , './xsim'),
        ('sim.top.*.cosim_intf', 'xsim'),
        ('sim.top.sink.fileset', ['/home/bvukobratovic/projects/sydpy/tests/sink.sv']),
        ('sim.top'          , TestDff),
        ('sim.duration'     , 100)
        ]

system.set_config(conf)
system.sim.run()
