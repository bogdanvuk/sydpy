import sydpy
from tests.packer_algo_tl import PackerTlAlgo
from tests.packer_tl_matrix import PackerTlMatrix

class Converter(sydpy.Component):
    @sydpy.compinit
    def __init__(self, name, parent, ch_sample, tSample = None):
        super().__init__(name, parent)
        
        self.N = N
        self.CS = CS
        ch_sample <<= sydpy.isig('sample', self, dtype=tSample, dflt={'d': 0, 'cs':0})

        sydpy.Process('p_gen', self, self.gen)
        self.rnd_gen = sydpy.rnd(sydpy.Bit(N + CS))
        
    def gen(self):
        for r in self.rnd_gen:
            self['sample'].bpush({'d': r[0:self.N-1], 'cs': r[self.N:self.N+self.CS-1]})
            
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

conf = [
        ('top.M'       , 16),
        ('top/*.CF'    , 1),
        ('top/*.CS'    , CS),
        ('top/*.F'     , 4),
        ('top/*.HD'    , 1),
        ('top/*.L'     , 7),
        ('top/*.S'     , 1),
        ('top/*.N'     , N),
        ('sim.duration', 10)
        ]

sydpy.ddic.configure('top/*.tSample', sydpy.Struct(('d', sydpy.Bit(N)), 
                                             ('cs', sydpy.Bit(CS))))


for c, v in conf:
    sydpy.ddic.configure(c, v)

sydpy.ddic.provide_on_demand('cls/sim', sydpy.Simulator, 'sim')
sydpy.ddic.provide('scheduler', sydpy.Scheduler())
JesdPacking('top', None)
sydpy.ddic['sim'].run()
