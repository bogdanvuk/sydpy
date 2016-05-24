from sydpy.cosim import Cosim
from sydpy.intfs.isig import Isig
from sydpy.types.bit import bit32, bit8
from sydpy.component import Component, inst
from sydpy.types import bit
from sydpy.process import Process
from sydpy.procs.clk import Clocking
from ddi.ddi import ddic, diinit, Dependency
from sydpy.channel import Channel
from sydpy.simulator import Simulator, Scheduler
from sydpy.xsim import XsimIntf
from sydpy.server import Server
import os
from sydpy.verif.basic_rnd_seq import BasicRndSeq
from sydpy.intfs.iseq import Iseq
from sydpy.types.struct import Struct

def teardown_function(function):
    ddic.clear()

def test_struct_intf():
    class CompCosim(Cosim):
        def __init__(self, name, din, 
                     clk:Dependency('clocking/clk'),
                     dtype=None,
                     fileset=[os.path.join(os.path.dirname(__file__), 'test_cosim_struct_intf.vhd')],
                     module_name='test_cosim_struct_intf'):
            
            diinit(super().__init__)(name, fileset, module_name)
            din >> self.inst(Iseq, 'din', dtype=dtype, clk=clk)

    class TestDominoes(Component):
        def __init__(self, name):
            super().__init__(name)
            
            self.inst(Channel, 'ch_data')

            self.inst(BasicRndSeq, 'gen', seq_o=self.ch_data)
            self.inst(CompCosim, 'cosim', din=self.ch_data)
   
    ddic.configure('sim.duration'         , 1000)
    dtype = Struct(('data', bit8), 
                   ('user', bit))
    ddic.configure('top/cosim.dtype'        , dtype)
    ddic.configure('top/gen.dtype'          , dtype)
    ddic.provide_on_demand('cls/sim', Simulator, 'sim')
    ddic.provide('scheduler', Scheduler())
    ddic.provide_on_demand('cls/xsimintf', XsimIntf, 'xsimintf', inst_kwargs=dict(builddir=os.path.join(os.path.dirname(__file__), 'xsimintf')))
    ddic.provide_on_demand('cls/xsimserver', Server,'xsimserver')
    inst(Clocking, 'clocking')
    inst(TestDominoes, 'top')
    
    ddic['sim'].run()

test_struct_intf()

