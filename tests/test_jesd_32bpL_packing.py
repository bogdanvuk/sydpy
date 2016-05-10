import sydpy
from tests.packer_algo_tl import PackerTlAlgo
from sydpy.verif.scoreboard import Scoreboard
from ddi.ddi import Dependency
from sydpy.component import inst
from tests.jesd_converter import Converter
from tests.jesd_32bpL_lookup_packer import Jesd32bpLLookupPacker
from sydpy.intfs.itlm import Itlm
from sydpy.types.array import Array
from sydpy.types._type_base import convgen

class FrameScoreboard(Scoreboard):
    def __init__(self, 
                 name, 
                 pack_algo_frame: Dependency('top/pack_algo/frame'),
                 pack_matrix_frame: Dependency('top/pack_lookup/frame')
                 ):
        super().__init__(name, [pack_algo_frame, pack_matrix_frame])

class Oversampler(sydpy.Component):
    def __init__ (self, name, ch_samples, ch_oversamples, 
                  tSample=None, 
                  jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0)):
        
        super().__init__(name)
        self.oversample_dtype = Array(tSample, jesd_params['S']*(1 if jesd_params['F'] >= 4 else int(4 / jesd_params['F'])))
        self.isamples = []
        self.ioversamples = []
        for i in range(jesd_params['M']):
            sample = self.inst(Itlm, 'sample{}'.format(i), tSample)
            oversample = self.inst(Itlm, 'oversample{}'.format(i), self.oversample_dtype)
            ch_samples[i] >>= sample
            ch_oversamples[i] <<= oversample
            self.isamples.append(sample)
            self.ioversamples.append(oversample)

        self.inst(sydpy.Process, 'proc_oversample', self.proc_oversample)

    def proc_oversample(self):
        while(1):
            for sample, oversample in zip(self.isamples, self.ioversamples):
                dout = self.oversample_dtype()
                while not dout._full():
                    din = sample.bpop()
                    for d,_ in convgen(din, self.oversample_dtype, dout):
                        if d._full():
                            oversample.bpush(d)
      
class JesdPacking(sydpy.Component):
    def __init__ (self, name, jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0)):
        super().__init__(name)

        self.ch_samples = []
        self.ch_oversamples = []
        self.conv = []
        self.ioversample = []
        for i in range(jesd_params['M']):
            ch = self.inst(sydpy.Channel, 'ch_sample{}'.format(i))
            self.ch_samples.append(ch)
            ch = self.inst(sydpy.Channel, 'ch_oversample{}'.format(i))
            self.ch_oversamples.append(ch)
            
            self.inst(Converter, 'conv{}'.format(i), ch_sample=self.ch_samples[-1], N=jesd_params['N'], CS=jesd_params['CS'])
        
#        self.inst(PackerTlAlgo, 'pack_algo', ch_samples=ch_gen)
        self.inst(Oversampler, 'oversampler', ch_samples=self.ch_samples, ch_oversamples=self.ch_oversamples) 
        self.inst(Jesd32bpLLookupPacker, 'pack_lookup', ch_samples=self.ch_oversamples)

N = 16
CS = 0
M = 2

sydpy.ddic.configure('sim.duration'         , 100)
#sydpy.ddic.configure('top/pack_matrix.arch' , 'tlm')
sydpy.ddic.configure('*.jesd_params'    , dict(M=M, CF=0, CS=CS, F=1, HD=1, L=4, S=1, N=N))
sydpy.ddic.configure('top/*.tSample'    , sydpy.Struct(('d', sydpy.Bit(N)), 
                                                       ('cs', sydpy.Bit(CS))))
sydpy.ddic.provide_on_demand('cls/sim', sydpy.Simulator, 'sim') # inst_kwargs=dict(log_signal_updates=True, log_event_triggers=True, log_task_switching=True))
sydpy.ddic.provide('scheduler', sydpy.Scheduler())
# sydpy.ddic.provide_on_demand('verif/cls/', FrameScoreboard, 'verif/inst/', inst_args=('verif'))#, 'verif/inst/')
#inst(FrameScoreboard, 'verif/inst/')
clk = inst(sydpy.Clocking, 'clocking')
sydpy.ddic.configure('top/*.clk', clk.c['clk'])
inst(JesdPacking, 'top')

sydpy.ddic['sim'].run()

for s in sydpy.ddic.search('verif/inst/*', assertion=lambda obj: isinstance(obj, Scoreboard)):
    assert len(sydpy.ddic[s].scoreboard_results['fail']) == 0

# import cProfile
# cProfile.run("sydpy.ddic['sim'].run()", sort='tottime')


