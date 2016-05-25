import sydpy
from tests.packer_algo_tl import PackerTlAlgo
from sydpy.verif.scoreboard import Scoreboard
from ddi.ddi import Dependency, diinit
from sydpy.component import inst, Component
from tests.jesd_converter import Converter
from tests.jesd_32bpL_lookup_packer import Jesd32bpLLookupPacker
from sydpy.intfs.itlm import Itlm
from sydpy.types.array import Array
from sydpy.types._type_base import convgen
from tests.jesd_packer_lookup_gen import create_lookup
from sydpy.cosim import Cosim
from sydpy.extens.tracing import VCDTracer
from sydpy.xsim import XsimIntf
from sydpy.server import Server
from sydpy.types.bit import Bit
from sydpy.intfs.isig import Isig
from sydpy.types import bit
from sydpy.intfs.iseq import FlowCtrl
from sydpy.process import Process

# jesd_params = dict(M=3, N=8, S=2, CS=2, CF=0, L=1, F=8, HD=0)
# frame_lookup = create_lookup(jesd_params, sample_flatten=True)

# print()
# print('Matrix Output Frame:')
# print()
# for l in frame_lookup:
#     print(l)
# 
# 
# import sys
# sys.exit(0)

class FrameScoreboard(Scoreboard):
    def __init__(self, 
                 name, 
                 cosim_packer_frame: Dependency('top/jesd_packer/frame_out'),
                 lookup_packer_frame: Dependency('top/pack_lookup/frame_out')
                 ):
        super().__init__(name, [cosim_packer_frame, lookup_packer_frame])

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
            ch_samples[i] >> sample
            ch_oversamples[i] << oversample
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

class JesdDataLink(Component):
    def __init__(self, name, tx_data, rx_data, tx_start_of_frame, clk:Dependency('clocking/clk'), jesd_params=None):
        super().__init__(name)
        tx_data             >> self.inst(sydpy.Iseq, 'tx_data', 
                                         dtype      =Bit(32*jesd_params['L']), 
                                         flow_ctrl  =FlowCtrl.ready, 
                                         trans_ctrl =False, 
                                         clk        =clk)
        self.tx_data.ready <<= True

        rx_data             << self.inst(sydpy.Iseq, 'rx_data', 
                                         dtype      =Bit(32*jesd_params['L']), 
                                         flow_ctrl  =FlowCtrl.valid, 
                                         trans_ctrl =False, 
                                         clk        =clk)
        tx_start_of_frame   << self.inst(sydpy.Iseq, 'tx_start_of_frame', 
                                         dtype      =Bit(4), 
                                         flow_ctrl  =FlowCtrl.none, 
                                         trans_ctrl =False, 
                                         clk        =clk)
        
        self.inst(Process, func=self.p_tx_start_of_frame, senslist=[clk.e.posedge])
        if jesd_params['F'] == 1:
            self.tx_start_of_frame <<= 0xf
        elif jesd_params['F'] == 2:
            self.tx_start_of_frame <<= 0x5
        else:
            self.tx_start_of_frame <<= 0x1
        
        self.frame_start_cnt = 0
        self.jesd_params = jesd_params
        
    def p_tx_start_of_frame(self):
        if self.jesd_params['F'] > 4:
            self.frame_start_cnt += 1
            self.frame_start_cnt &= (int(self.jesd_params['F']/4) - 1) 
            
            if self.frame_start_cnt == 0:
                self.tx_start_of_frame <<= 0
            else:
                self.tx_start_of_frame <<= 0x1
                
        self.rx_data        <<= self.tx_data.data()
        self.rx_data.valid  <<= True 
                
class JesdPackerCosim(Cosim):
    def __init__(self, name, frame_out, tx_start_of_frame, ch_samples, clk:Dependency('clocking/clk')=None, jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0), 
                 fileset=['/home/bvukobratovic/projects/sydpy/tests/packing/jesd_packer_rtl.vhd']):
        diinit(super().__init__)(name, fileset)
        
        frame_out           << self.inst(sydpy.Iseq, 'tx', 
                                         dtype      = Bit(32*jesd_params['L']), 
                                         flow_ctrl  = FlowCtrl.ready, 
                                         trans_ctrl = False, 
                                         clk        = clk)
        
        tx_start_of_frame   >> self.inst(sydpy.Iseq, 'tx_start_of_frame', 
                                         dtype      = Bit(4), 
                                         flow_ctrl  = FlowCtrl.none, 
                                         trans_ctrl = False, 
                                         clk        = clk)
 
        self.overframe_num = (1 if jesd_params['F'] >= 4 else int(4 / jesd_params['F']))
        self.oversample_num = jesd_params['S']*self.overframe_num
        single_converter_vector_w = self.oversample_num*(jesd_params['N'] + jesd_params['CS'])
        self.input_vector_w = jesd_params['M']*single_converter_vector_w
         
        idin = self.inst(sydpy.Iseq, 'din', dtype=Bit(self.input_vector_w), dflt=0, clk=clk)
        clk >> self.inst(Isig, 'clk', dtype=bit)
#         self.clk._connect(clk)
         
        for i, d in enumerate(ch_samples):
            d >> idin[i*single_converter_vector_w : (i+1)*single_converter_vector_w - 1]
            
#         self.inst(sydpy.Process, 'pack', self.pack, senslist=[idin.clk.e.posedge])
#      
#     def pack(self):
#         print('COSIM DIN: ', self.din.data())
#         print('COSIM VALID: ', self.din.last())
#         print('COSIM LAST: ', self.din.valid())
#         print('COSIM READY: ', self.din.valid())
            
        
            
# class JesdPackerCosim(sydpy.Component):
#     def __init__(self, name, frame_out, ch_samples, jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0)):
#         diinit(super().__init__)(name)
#         frame_out <<= self.inst(sydpy.Isig, 'frame_out', dtype=Bit(32*jesd_params['L']))
#  
#         self.overframe_num = (1 if jesd_params['F'] >= 4 else int(4 / jesd_params['F']))
#         self.oversample_num = jesd_params['S']*self.overframe_num
#         single_converter_vector_w = self.oversample_num*(jesd_params['N'] + jesd_params['CS'])
#         self.input_vector_w = jesd_params['M']*single_converter_vector_w
#          
#         idin = self.inst(sydpy.Iseq, 'din', dtype=Bit(self.input_vector_w), dflt=0)
#          
#         for i, d in enumerate(ch_samples):
#             d >>= idin[i*single_converter_vector_w : (i+1)*single_converter_vector_w - 1]
#          
#         self.inst(sydpy.Process, 'pack', self.pack, senslist=[idin.clk.e.posedge])
#      
#     def pack(self):
#         print('COSIM DIN: ', self.din.data())
#         print('COSIM VALID: ', self.din.last())
#         print('COSIM LAST: ', self.din.valid())

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
        
        for ch in ['tx_data', 'rx_data', 'frame_out', 'tx_start_of_frame']:
            self.inst(sydpy.Channel, ch)
        
#        self.inst(PackerTlAlgo, 'pack_algo', ch_samples=ch_gen)
        self.inst(Oversampler, 'oversampler', 
                  ch_samples        = self.ch_samples, 
                  ch_oversamples    = self.ch_oversamples)
        
        self.inst(Jesd32bpLLookupPacker, 'pack_lookup', 
                  frame_out         = self.frame_out, 
                  ch_samples        = self.ch_oversamples)
        
        self.inst(JesdPackerCosim, 'jesd_packer', 
                  frame_out         = self.tx_data,
                  ch_samples        = self.ch_oversamples,
                  tx_start_of_frame = self.tx_start_of_frame)
        
        self.inst(JesdDataLink, 'jesd',
                  tx_data           = self.tx_data,
                  rx_data           = self.rx_data,
                  tx_start_of_frame = self.tx_start_of_frame)

N = 16
CS = 0

sydpy.ddic.configure('sim.duration'         , 600)
#sydpy.ddic.configure('top/pack_matrix.arch' , 'tlm')
sydpy.ddic.configure('*.jesd_params'    , dict(M=8, CF=0, CS=CS, F=8, HD=1, L=4, S=2, N=N))
sydpy.ddic.configure('top/*.tSample'    , sydpy.Struct(('d', sydpy.Bit(N)), 
                                                       ('cs', sydpy.Bit(CS))))
#sydpy.ddic.configure('top.jesd_packer.fileset', ['/home/bvukobratovic/projects/sydpy/tests/packing/jesd_packer_rtl.vhd'])
sydpy.ddic.provide_on_demand('cls/sim', sydpy.Simulator, 'sim') # inst_kwargs=dict(log_signal_updates=True, log_event_triggers=True, log_task_switching=True))
sydpy.ddic.provide('scheduler', sydpy.Scheduler())
sydpy.ddic.provide_on_demand('cls/tracing', VCDTracer, 'tracing')

sydpy.ddic.provide_on_demand('cls/xsimserver', Server,'xsimserver')
sydpy.ddic.provide_on_demand('cls/xsimintf', XsimIntf, 'xsimintf')
# sydpy.ddic.provide_on_demand('verif/cls/', FrameScoreboard, 'verif/inst/', inst_args=('verif'))#, 'verif/inst/')
inst(FrameScoreboard, 'verif/inst/')
clk = inst(sydpy.Clocking, 'clocking')
# sydpy.ddic.configure('top/*.clk', clk.clk)
inst(JesdPacking, 'top')

sydpy.ddic['sim'].run()

for s in sydpy.ddic.search('verif/inst/*', assertion=lambda obj: isinstance(obj, Scoreboard)):
    assert len(sydpy.ddic[s].scoreboard_results['fail']) == 0

