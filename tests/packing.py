import sydpy
from tests.packer_algo_tl import PackerTlAlgo
from sydpy.verif.scoreboard import Scoreboard
from ddi.ddi import Dependency
from sydpy.component import inst
from tests.jesd_frame_lookup_packer import JesdFrameLookupPacker
from tests.jesd_converter import Converter

class FrameScoreboard(Scoreboard):
    def __init__(self, 
                 name, 
                 pack_algo_frame: Dependency('top/pack_algo/frame'),
                 pack_matrix_frame: Dependency('top/pack_lookup/frame')
                 ):
        super().__init__(name, [pack_algo_frame, pack_matrix_frame])
         
class JesdPacking(sydpy.Component):
    def __init__ (self, name, jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0)):
        super().__init__(name)

        ch_gen = []
        for i in range(jesd_params['M']):
            ch_gen.append(self.inst(sydpy.Channel, 'ch_gen{}'.format(i)))
            self.inst(Converter, 'conv{}'.format(i), ch_sample=ch_gen[-1], N=jesd_params['N'], CS=jesd_params['CS'])
            
        self.inst(PackerTlAlgo, 'pack_algo', ch_samples=ch_gen)
        self.inst(JesdFrameLookupPacker, 'pack_lookup', ch_samples=ch_gen)

N = 11
CS = 2
M = 16

sydpy.ddic.configure('sim.duration'         , 100)
#sydpy.ddic.configure('top/pack_matrix.arch' , 'tlm')
sydpy.ddic.configure('*.jesd_params'    , dict(M=M, CF=1, CS=CS, F=4, HD=1, L=7, S=1, N=N))
sydpy.ddic.configure('top/*.tSample'    , sydpy.Struct(('d', sydpy.Bit(N)), 
                                                       ('cs', sydpy.Bit(CS))))
sydpy.ddic.provide_on_demand('cls/sim', sydpy.Simulator, 'sim')
sydpy.ddic.provide('scheduler', sydpy.Scheduler(log_task_switching=False))
# sydpy.ddic.provide_on_demand('verif/cls/', FrameScoreboard, 'verif/inst/', inst_args=('verif'))#, 'verif/inst/')
inst(FrameScoreboard, 'verif/inst/')
inst(JesdPacking, 'top')

sydpy.ddic['sim'].run()

for s in sydpy.ddic.search('verif/inst/*', assertion=lambda obj: isinstance(obj, Scoreboard)):
    assert len(sydpy.ddic[s].scoreboard_results['fail']) == 0

# import cProfile
# cProfile.run("sydpy.ddic['sim'].run()", sort='tottime')


