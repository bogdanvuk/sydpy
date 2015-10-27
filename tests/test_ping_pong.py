from sydpy.configurator import Configurator
from sydpy.component import Component, system, compinit
from sydpy.unit import Unit
from sydpy.channel import Channel
from sydpy.intfs.isig import isig
from sydpy.types import bit8, bit, bit64, bit32
from sydpy._delay import Delay
from sydpy.module import proc, Module
from sydpy.process import Process
from sydpy.simulator import Simulator
from sydpy.cosim import Cosim
from sydpy.xsim import XsimIntf
from sydpy.server import Server

class Generator(Component):
    
    @compinit 
    def __init__(self, chout, dtype=bit8, **kwargs):
        chout <<= self.inst('sout', isig, dtype=dtype, dflt=0)
        self.inst('p_gen', Process, self.gen, [Delay(20)])
    def gen(self):
        self.sout <<= self.sout + 1
        print("GEN : ", system['sim'].time, ': ', self.sout.read() + 1)
        

# class Sink(Cosim):
#     @compinit
#     def __init__(self, chin, chout, dtype=bit, **kwargs):
#         chin >>= self.inst('din', isig, dtype=dtype, dflt=0)
#         chout <<= self.inst('dout', isig, dtype=dtype, dflt=0)

class Ping(Component):
    @compinit
    def __init__(self, chin, chout, chgen, dtype=bit, **kwargs):
        chin >>= self.inst('din', isig, dtype=dtype, dflt=0)
        chout <<= self.inst('dout', isig, dtype=dtype, dflt=0)
        chgen >>= self.inst('gen', isig, dtype=bit8, dflt=0)
        self.inst('p_ping', Process, self.ping)
        
    def ping(self):
        print("PONG : ", system['sim'].time, ': ', self.din)
        self.dout <<= self.din[23:16] % self.din[15:8] % self.din[7:0] % self.gen 

class Pong(Component):
    @compinit
    def __init__(self, chin, chout, dtype=bit, **kwargs):
        chin >>= self.inst('din', isig, dtype=dtype, dflt=0)
        chout <<= self.inst('dout', isig, dtype=dtype, dflt=0)
        self.inst('p_pong', Process, self.pong)
        
    def pong(self):
        print("PING : ", system['sim'].time, ': ', self.din)
        self.dout <<= self.din

# class Printout(Component):
#     @compinit
#     def __init__(self, chin, dtype=bit, **kwargs):
#         chin >>= self.inst('sin', isig, dtype=dtype, dflt=0)
#         self.inst('p_sink', Process, self.psink)
# 
#     def psink(self):
#         print(system['sim'].time, ': ', self.sin)
    
class TestDff(Component):
    @compinit
    def __init__ (self, name):
        for ch in ['ch_gen', 'ch_ping', 'ch_pong']:
            self.inst(ch, Channel)
            
        self.inst('gen', Generator, chout=self.ch_gen)
        self.inst('ping', Ping, chin=self.ch_pong, chout=self.ch_ping, chgen=self.ch_gen)
        self.inst('pong', Pong, chin=self.ch_ping, chout=self.ch_pong)
#         self.inst('print', Printout, chin=self.ch_out)

conf = [
        ('sim'              , Simulator),
#         ('xsim'             , XsimIntf),
#         ('server'           , Server),
        ('xsim.builddir'    , './xsim'),
        ('sim.top.*.cosim_intf', 'xsim'),
        ('sim.top.sink.fileset', ['/home/bvukobratovic/projects/sydpy/tests/sink.sv']),
        ('sim.top'          , TestDff),
        ('sim.top.ping.dtype'  , bit32),
        ('sim.top.pong.dtype'  , bit32),
        ('sim.duration'     , 10000)
        ]

system.set_config(conf)
system.sim.run()
