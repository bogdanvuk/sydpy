import sydpy
from tests.packer_algo_tl import PackerTlAlgo
from tests.packer_tl_matrix import PackerTlMatrix
from sydpy.verif.scoreboard import Scoreboard
from ddi.ddi import Dependency
from sydpy.component import inst

class Converter(sydpy.Component):
    def __init__(self, name, ch_sample, tSample = None):
        super().__init__(name)
        
        self.N = N
        self.CS = CS
        ch_sample <<= self.inst(sydpy.Itlm, 'sample', dtype=tSample, dflt={'d': 0, 'cs':0})

        self.inst(sydpy.Process, 'p_gen', self.gen)
        self.rnd_gen = sydpy.rnd(sydpy.Bit(N + CS))
        
    def gen(self):
        for r in self.rnd_gen:
            self.c['sample'].bpush({'d': r[0:self.N-1], 'cs': r[self.N:self.N+self.CS-1]})

class FrameScoreboard(Scoreboard):
    def __init__(self, 
                 name, 
                 pack_algo_frame: Dependency('top/pack_algo/frame'),
                 pack_matrix_frame: Dependency('top/pack_matrix/frame')
                 ):
        super().__init__(name, [pack_algo_frame, pack_matrix_frame])
         
class JesdPacking(sydpy.Component):
    def __init__ (self, name, M=1):
        super().__init__(name)

        ch_gen = []
        for i in range(M):
            ch_gen.append(self.inst(sydpy.Channel, 'ch_gen{}'.format(i)))
            self.inst(Converter, 'conv{}'.format(i), ch_sample=ch_gen[-1])
            
        self.inst(PackerTlAlgo, 'pack_algo', ch_samples=ch_gen)
        self.inst(PackerTlMatrix, 'pack_matrix', ch_samples=ch_gen)

N = 11
CS = 2
M = 16

sydpy.ddic.configure('sim.duration'         , 100)
sydpy.ddic.configure('top/pack_matrix.arch' , 'seq')
sydpy.ddic.configure('top/*.jesd_params'    , dict(M=M, CF=1, CS=CS, F=4, HD=1, L=7, S=1, N=N))
sydpy.ddic.configure('top.M'                , M)
sydpy.ddic.configure('top/*.tSample'        , sydpy.Struct(('d', sydpy.Bit(N)), 
                                                           ('cs', sydpy.Bit(CS))))
# for c, v in conf:
#     sydpy.ddic.configure(c, v)

sydpy.ddic.provide_on_demand('cls/sim', sydpy.Simulator, 'sim')
sydpy.ddic.provide('scheduler', sydpy.Scheduler(log_task_switching=True))
#sydpy.ddic.provide_on_demand('verif/cls/', FrameScoreboard)#, 'verif/inst/')

clk = inst(sydpy.Clocking, 'clocking')
sydpy.ddic.configure('top/*.clk', clk.c['clk'])
inst(JesdPacking, 'top')

sydpy.ddic['sim'].run()

# import cProfile
# cProfile.run("sydpy.ddic['sim'].run()", sort='tottime')


