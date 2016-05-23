from sydpy.cosim import Cosim
from sydpy.intfs.isig import Isig
from sydpy.types.bit import bit32
from sydpy.component import Component, inst
from sydpy.types import bit
from sydpy.process import Process
from sydpy.procs.clk import Clocking
from ddi.ddi import ddic, diinit
from sydpy.channel import Channel
from sydpy.simulator import Simulator, Scheduler
from sydpy.xsim import XsimIntf
from sydpy.server import Server
import os

def teardown_function(function):
    ddic.clear()

def test_dominoes():
    class CosimDominoes(Cosim):
        def __init__(self, name, trigger, last, 
                     fileset=[os.path.join(os.path.dirname(__file__), 'dominoes_test.vhd')],
                     module_name='dominoes_test'):
            
            diinit(super().__init__)(name, fileset, module_name)
            trigger >>= self.inst(Isig, 'trigger', dtype=bit)
            last <<= self.inst(Isig, 'last', dtype=bit)
    
    class Trigger(Component):
        def __init__(self, name, trigger, clk=None):
            super().__init__(name)
            
            trigger <<= self.inst(Isig, 'trigger', dtype=bit, dflt=0)
            self.inst(Process, func=self.proc_trigger, senslist=[clk.e.posedge])
            
        def proc_trigger(self):
            self.trigger <<= not self.trigger()
    
    class Dominoes(Component):
        def __init__(self, name, trigger, last):
            super().__init__(name)
            
            trigger >>= self.inst(Isig, 'trigger', dtype=bit)
            last <<= self.inst(Isig, 'last', dtype=bit, dflt=0)
            
            self.inst(Isig, 'dominoes', dtype=bit32, dflt=0)
            
            self.inst(Process, func=self.proc_dominoes)
            
        def proc_dominoes(self):
            self.dominoes[0] <<= self.trigger()
            for i in range(1, 32):
                self.dominoes[i] <<= self.dominoes[i-1]()
                
            self.last <<= self.dominoes[31]() 
    
    class TestDominoes(Component):
        def __init__(self, name):
            super().__init__(name)
            
            for chname in ['ch_trigger', 'ch_last_dominoe', 'ch_last_cosim_dominoe']:
                self.inst(Channel, chname)
            
            self.inst(Trigger, 'trigger', trigger=self.ch_trigger)
            self.inst(Dominoes, 'dominoes', trigger=self.ch_trigger, last=self.ch_last_dominoe)
            self.inst(CosimDominoes, 'cosim_dominoes', trigger=self.ch_last_dominoe, last=self.ch_last_cosim_dominoe)
    
    ddic.configure('sim.duration'         , 1000)
    ddic.provide_on_demand('cls/sim', Simulator, 'sim')
    ddic.provide('scheduler', Scheduler())
    ddic.provide_on_demand('cls/xsimintf', XsimIntf, 'xsimintf', inst_kwargs=dict(builddir=os.path.join(os.path.dirname(__file__), 'xsimintf')))
    ddic.provide_on_demand('cls/xsimserver', Server,'xsimserver')
    clk = inst(Clocking, 'clocking')
    ddic.configure('top/*.clk', clk.clk)
    inst(TestDominoes, 'top')
    
    def delta_monitor(sim):
        print(sim.time, sim.delta_count)
#         if sim.time % 100 == 0:
#             assert sim.delta_count == 1
#         elif sim.time % 100 == 50:
#             assert sim.delta_count == 36
#             if int(sim.time/100) % 2 == 0:
#                 assert ddic['top/cosim_dominoes/last']() == 1
#             else:
#                 assert ddic['top/cosim_dominoes/last']() == 0
#         else:
#             print(sim.time)
#             assert False
        return True
    
    ddic['sim'].events['delta_settled'].append(delta_monitor)
    ddic['sim'].run()

test_dominoes()

