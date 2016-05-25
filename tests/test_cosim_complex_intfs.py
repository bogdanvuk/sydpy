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
from sydpy.verif.scoreboard import Scoreboard

def teardown_function(function):
    ddic.clear()

def test_struct_intf():
    class CompCosim(Cosim):
        def __init__(self, name, din, dout,
                     clk:Dependency('clocking/clk'),
                     dtype=None,
                     fileset=[os.path.join(os.path.dirname(__file__), 'test_cosim_struct_intf.vhd')],
                     module_name='test_cosim_struct_intf'):
            
            diinit(super().__init__)(name, fileset, module_name)
            din >> self.inst(Iseq, 'din', dtype=dtype, clk=clk)
            dout << self.inst(Iseq, 'dout', dtype=dtype, clk=clk)

    class TestDominoes(Component):
        def __init__(self, name):
            super().__init__(name)
            
            for ch in ['ch_din', 'ch_dout']:
                self.inst(Channel, ch)

            self.inst(BasicRndSeq, 'gen', seq_o=self.ch_din)
            self.inst(CompCosim, 'cosim', din=self.ch_din, dout=self.ch_dout)
   
    class CosimScoreboard(Scoreboard):
        def __init__(self, 
                     name, 
                     cosim_packer_frame: Dependency('top/gen/seq'),
                     lookup_packer_frame: Dependency('top/cosim/dout')
                     ):
            super().__init__(name, [cosim_packer_frame, lookup_packer_frame])

    ddic.configure('sim.duration'         , 1000)
    dtype = Struct(('data', bit8), 
                   ('user', bit),
                   ('dest', bit8))
    ddic.configure('top/cosim.dtype'        , dtype)
    ddic.configure('top/gen.dtype'          , dtype)
    ddic.provide_on_demand('cls/sim', Simulator, 'sim')
    ddic.provide('scheduler', Scheduler())
    ddic.provide_on_demand('cls/xsimintf', XsimIntf, 'xsimintf', inst_kwargs=dict(builddir=os.path.join(os.path.dirname(__file__), 'xsimintf')))
    ddic.provide_on_demand('cls/xsimserver', Server,'xsimserver')
    
    inst(CosimScoreboard, 'verif/inst/')
    inst(Clocking, 'clocking')
    inst(TestDominoes, 'top')
    
    ddic['sim'].run()
    
    for s in ddic.search('verif/inst/*', assertion=lambda obj: isinstance(obj, Scoreboard)):
        assert len(ddic[s].scoreboard_results['fail']) == 0

test_struct_intf()

