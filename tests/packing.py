import sydpy
from tests.packer_algo_tl import PackerTlAlgo
from tests.packer_tl_matrix import PackerTlMatrix
from sydpy.verif.scoreboard import Scoreboard
from ddi.ddi import Dependency

class Converter(sydpy.Component):
    @sydpy.compinit
    def __init__(self, name, parent, ch_sample, tSample = None):
        super().__init__(name, parent)
        
        self.N = N
        self.CS = CS
        ch_sample <<= sydpy.Itlm('sample', self, dtype=tSample, dflt={'d': 0, 'cs':0})

        sydpy.Process('p_gen', self, self.gen)
        self.rnd_gen = sydpy.rnd(sydpy.Bit(N + CS))
        
    def gen(self):
        for r in self.rnd_gen:
            self.c['sample'].bpush({'d': r[0:self.N-1], 'cs': r[self.N:self.N+self.CS-1]})

class FrameScoreboard(Scoreboard):
    
    def __init__(self, 
                 pack_algo_frame: Dependency('top/pack_algo/frame'),
                 pack_matrix_frame: Dependency('top/pack_matrix/frame')
                 ):
        super().__init__('frame_scoreboard', None, [pack_algo_frame, pack_matrix_frame])
         
class JesdPacking(sydpy.Component):
    @sydpy.compinit
    def __init__ (self, name, parent, M=1, **kwargs):
        super().__init__(name, parent)
#         for ch in ['ch_gen', 'ch_ping', 'ch_pong']:
#             self.inst(ch, Channel)
        
        ch_gen = []
        for i in range(M):
            ch_gen.append(sydpy.Channel('ch_gen{}'.format(i), self))
            Converter('conv{}'.format(i), self, ch_sample=ch_gen[-1])
            
        PackerTlAlgo('pack_algo', self, ch_samples=ch_gen)
        PackerTlMatrix('pack_matrix', self, ch_samples=ch_gen)

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

clk = sydpy.Clocking('clocking', None)
sydpy.ddic.configure('top/*.clk', clk.c['clk'])
top = JesdPacking('top', None)

sydpy.ddic['sim'].run()

# import cProfile
# cProfile.run("sydpy.ddic['sim'].run()", sort='tottime')


