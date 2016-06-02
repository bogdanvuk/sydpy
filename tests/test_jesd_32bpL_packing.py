import sydpy
from sydpy.verif.scoreboard import Scoreboard
from ddi.ddi import Dependency, diinit
from sydpy.component import inst, Component
from tests.jesd_converter import Converter
from tests.jesd_32bpL_lookup_packer import Jesd32bpLLookupPacker,\
    Jesd32bpLLookupUnpacker
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
from collections import OrderedDict
from sydpy.verif.basic_rnd_seq import BasicRndSeq
from sydpy.types.struct import Struct

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
    def __init__(self, name, tx_data, rx_data, tx_start_of_frame, rx_start_of_frame, 
                 clk:Dependency('clocking/clk'), jesd_params=None):
        super().__init__(name)
        tx_data             >> self.inst(sydpy.Iseq, 'tx_data', 
                                         dtype      =Bit(32*jesd_params['L']), 
                                         flow_ctrl  =FlowCtrl.ready, 
                                         trans_ctrl =False, 
                                         clk        =clk)
        rx_data             << self.inst(sydpy.Iseq, 'rx_data', 
                                         dtype      =Bit(32*jesd_params['L']), 
                                         flow_ctrl  =FlowCtrl.valid, 
                                         trans_ctrl =False, 
                                         clk        =clk)
        tx_start_of_frame   << self.inst(sydpy.Iseq, 'tx_start_of_frame', 
                                         dtype      =Bit(jesd_params['L']), 
                                         flow_ctrl  =FlowCtrl.none, 
                                         trans_ctrl =False, 
                                         dflt       =0,
                                         clk        =clk)

        rx_start_of_frame   << self.inst(sydpy.Iseq, 'rx_start_of_frame', 
                                         dtype      =Bit(jesd_params['L']), 
                                         flow_ctrl  =FlowCtrl.none, 
                                         trans_ctrl =False, 
                                         dflt       =0,
                                         clk        =clk)
        
        self.inst(Process, func=self.p_tx_start_of_frame, senslist=[clk.e.posedge])
        
        self.init_delay = 0
        self.frame_start_cnt = 0
        self.jesd_params = jesd_params
        
    def p_tx_start_of_frame(self):
        if self.init_delay < 3:
            self.init_delay += 1
            self.tx_start_of_frame <<= 0x0
        elif self.init_delay == 3:
            self.tx_data.ready <<= True
            self.init_delay += 1
        else:
            if self.jesd_params['F'] == 1:
                self.tx_start_of_frame <<= 0xf
            elif self.jesd_params['F'] == 2:
                self.tx_start_of_frame <<= 0x5
            elif self.jesd_params['F'] == 4:
                self.tx_start_of_frame <<= 0x1
            else:
                if self.frame_start_cnt == 0:
                    self.tx_start_of_frame <<= 0x1
                else:
                    self.tx_start_of_frame <<= 0
                    
                self.frame_start_cnt += 1
                self.frame_start_cnt &= (int(self.jesd_params['F']/4) - 1) 
                
            self.rx_start_of_frame <<= self.tx_start_of_frame()
            self.rx_data        <<= self.tx_data.data()
            self.rx_data.valid  <<= True 
                
class JesdPackerCosim(Cosim):
    def __init__(self, name, 
                 tx_data, tx_start_of_frame, tx_samples, 
                 rx_data, rx_start_of_frame, rx_samples, 
                 clk:Dependency('clocking/clk')=None, 
                 jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0),
                 parameters=OrderedDict(),
                 fileset=['/home/bvukobratovic/projects/sydpy/tests/packing/jesd_packer_rtl.vhd']):
        
        diinit(super().__init__)(name, fileset=fileset, parameters=parameters)
        
        tx_data           << self.inst(sydpy.Iseq, 'tx', 
                                         dtype      = Bit(32*jesd_params['L']), 
                                         flow_ctrl  = FlowCtrl.ready, 
                                         trans_ctrl = False, 
                                         clk        = clk)
        
        tx_start_of_frame   >> self.inst(sydpy.Iseq, 'tx_start_of_frame', 
                                         dtype      = Bit(jesd_params['L']), 
                                         flow_ctrl  = FlowCtrl.none, 
                                         trans_ctrl = False, 
                                         clk        = clk)

        rx_data            >> self.inst(sydpy.Iseq, 'rx', 
                                         dtype      = Bit(32*jesd_params['L']), 
                                         flow_ctrl  = FlowCtrl.valid, 
                                         trans_ctrl = False, 
                                         clk        = clk)
        
        rx_start_of_frame   >> self.inst(sydpy.Iseq, 'rx_start_of_frame', 
                                         dtype      = Bit(jesd_params['L']),
                                         flow_ctrl  = FlowCtrl.none, 
                                         trans_ctrl = False, 
                                         clk        = clk)

        self.overframe_num = (1 if jesd_params['F'] >= 4 else int(4 / jesd_params['F']))
        self.oversample_num = jesd_params['S']*self.overframe_num
        single_converter_vector_w = self.oversample_num*(jesd_params['N'] + jesd_params['CS'])
        self.input_vector_w = jesd_params['M']*single_converter_vector_w

        self.inst(sydpy.Iseq, 'din', 
                  dtype=Bit(self.input_vector_w), 
                  dflt=0,
                  flow_ctrl  = FlowCtrl.ready, 
                  trans_ctrl = False, 
                  clk=clk)

        self.inst(sydpy.Iseq, 'dout', 
                  dtype=Bit(self.input_vector_w), 
                  dflt=0,
                  flow_ctrl  = FlowCtrl.valid, 
                  trans_ctrl = False, 
                  clk=clk)
       
        clk >> self.inst(Isig, 'clk', dtype=bit)
#         self.clk._connect(clk)
         
        for i, d in enumerate(tx_samples):
            d >> self.din[i*single_converter_vector_w : (i+1)*single_converter_vector_w - 1]

        for i, d in enumerate(rx_samples):
            d << self.dout[i*single_converter_vector_w : (i+1)*single_converter_vector_w - 1]


class JesdPacking(sydpy.Component):
    def __init__ (self, name, jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0)):
        super().__init__(name)

        oversampling_rate = jesd_params['S']*(1 if jesd_params['F'] >= 4 else int(4 / jesd_params['F']))

        self.ch_tx_samples = []
        self.ch_tx_oversamples = []
        self.ch_rx_samples = []
        self.ch_rx_oversamples = []
        self.gold_ch_rx_oversamples = []    
        self.conv = []
        self.ioversample = []

        for i in range(jesd_params['M']):
            self.ch_tx_oversamples.append(
                                          self.inst(sydpy.Channel, 'ch_oversample{}'.format(i)))

            self.inst(BasicRndSeq, 'oversampler{}'.format(i), 
                      seq_o=self.ch_tx_oversamples[-1], 
                      dtype=Array(Struct(('d', sydpy.Bit(N)), 
                                         ('cs', sydpy.Bit(CS))), 
                                  oversampling_rate))
             
            self.ch_rx_oversamples.append(
                                          self.inst(sydpy.Channel, 'ch_rx_oversample{}'.format(i)))
            self.gold_ch_rx_oversamples.append(
                                               self.inst(sydpy.Channel, 'gold_ch_rx_oversample{}'.format(i)))
        
        for ch in ['tx_data', 'rx_data', 'gold_rx_data', 'frame_out', 'tx_start_of_frame', 'rx_start_of_frame']:
            self.inst(sydpy.Channel, ch)
        
#        self.inst(PackerTlAlgo, 'pack_algo', ch_samples=ch_gen)
#         self.inst(Oversampler, 'oversampler', 
#                   ch_samples        = self.ch_tx_samples, 
#                   ch_oversamples    = self.ch_tx_oversamples)
        
        self.inst(Jesd32bpLLookupPacker, 'pack_lookup', 
                  frame_out         = self.frame_out, 
                  ch_samples        = self.ch_tx_oversamples)
        
        self.inst(JesdPackerCosim, 'jesd_packer', 
                  tx_data           = self.tx_data,
                  tx_samples        = self.ch_tx_oversamples,
                  tx_start_of_frame = self.tx_start_of_frame,

                  rx_data           = self.rx_data,
                  rx_samples        = self.ch_rx_oversamples,
                  rx_start_of_frame = self.rx_start_of_frame)
        
        self.inst(JesdDataLink, 'jesd',
                  tx_data           = self.tx_data,
                  rx_data           = self.rx_data,
                  tx_start_of_frame = self.tx_start_of_frame,
                  rx_start_of_frame = self.rx_start_of_frame
                  )
        
        self.inst(Jesd32bpLLookupUnpacker, 'unpack_lookup',
                  frame_in         = self.gold_rx_data, 
                  ch_samples       = self.gold_ch_rx_oversamples)
                  

N = 16
CS = 0
jesd_params = dict(M=4, CF=0, CS=CS, F=8, HD=1, L=2, S=2, N=N)

sydpy.ddic.configure('sim.duration'         , 1000)
#sydpy.ddic.configure('top/pack_matrix.arch' , 'tlm')
sydpy.ddic.configure('*.jesd_params'    , jesd_params)
sydpy.ddic.configure('top/jesd_packer.parameters'    , OrderedDict([('N_g', jesd_params['N']),
                                                                    ('CS_g', jesd_params['CS']),
                                                                    ('M_g', jesd_params['M']),
                                                                    ('S_g', jesd_params['S']),
                                                                    ('F_g', jesd_params['F']),
                                                                    ('L_g', jesd_params['L'])]))

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

for i in range(jesd_params['M']):
    inst(Scoreboard, 'verif/inst/', [sydpy.ddic['top/ch_rx_oversample{}'.format(i)], sydpy.ddic['top/oversampler{}/seq'.format(i)]])

sydpy.ddic['sim'].run()

for s in sydpy.ddic.search('verif/inst/*', assertion=lambda obj: isinstance(obj, Scoreboard)):
    assert len(sydpy.ddic[s].scoreboard_results['fail']) == 0

