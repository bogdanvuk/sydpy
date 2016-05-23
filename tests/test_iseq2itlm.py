from sydpy.component import Component, inst
from sydpy.intfs.isig import Isig
from sydpy._delay import Delay
from sydpy.process import Process
from sydpy.types.bit import bit8, bit16, Bit
from sydpy.channel import Channel
from sydpy import rnd
from sydpy.intfs.itlm import Itlm
from sydpy.intfs.iseq import Iseq
from ddi.ddi import ddic
from sydpy.simulator import Simulator, Scheduler
from sydpy.procs.clk import Clocking
from sydpy.types.array import Array
import itertools
import random

class Generator(Component):
    def __init__(self, name, chout, dtype=bit8, sequence_len=1, burst_len=1):
        super().__init__(name)
        
        chout <<= self.inst(Iseq, 'dout', dtype=dtype)
        self.inst(Process, func=self.sequence_gen, senslist=[self.dout.clk.e.posedge])
        self.rnd_gen = rnd(dtype)
        self.samples = [] 
        self.burst_len = burst_len
        self.sequence_len = sequence_len
        self.dtype = dtype
        self.sequence_cnt = 0
        self.burst_cnt = 0

        self.dout.data <<= next(self.rnd_gen)
        self.dout.valid <<= True
        if self.burst_len == 1:
            self.dout.last <<= True
        else:
            self.dout.last <<= False
        
    def sequence_gen(self):
        if len(self.samples) <= self.sequence_len:
            if self.dout.ready() and self.dout.valid():
                
                if self.burst_cnt == 0:
                    self.samples.append([])
                  
                self.samples[-1].append(self.dout.data())
                self.burst_cnt += 1
                self.dout.last <<= False
                self.dout.data <<= next(self.rnd_gen)
                self.dout.valid <<= True
    
                if self.burst_cnt == self.burst_len - 1:
                    self.dout.last <<= True
                elif self.burst_cnt == self.burst_len:
                    self.sequence_cnt += 1
                    self.burst_cnt = 0
                    if self.burst_len == 1:
                        self.dout.last <<= True
                    if len(self.samples) == self.sequence_len:
                        self.dout.valid <<= False
                
                
class Receiver(Component):
    def __init__(self, name, chin, dtype=bit8):
        super().__init__(name)
        
        chin >>= self.inst(Itlm, 'din', dtype=dtype)
#         slice_size = int(dtype.w / len(chin))
#         for i, ch in enumerate(chin):
#             ch >>= din[i*slice_size: (i+1)*slice_size - 1]
            
        self.inst(Process, func=self.proc, senslist=[])
        self.samples = []
        
    def proc(self):
        while(1):
            self.samples.append(self.din.bpop()) 
        
class TestIseq2Itlm(Component):
    def __init__ (self, name, gen_num=1):
        super().__init__(name)
        self.inst(Channel, 'ch_gen')
        self.inst(Receiver, 'recv', chin=self.ch_gen)
        self.inst(Generator, 'gen', chout=self.ch_gen)
        
#         chin=[]
#         for i in range(gen_num):
#             ch = self.inst(Channel, 'ch_gen{}'.format(i))
#             self.inst(Generator, 'gen{}'.format(i), chout=ch)
#             chin.append(ch)
#             
#         self.inst(Receiver, 'recv', chin=chin)

def teardown_function(function):
    ddic.clear()

def default_setup_and_run(duration):
    clk = inst(Clocking, 'clocking')
    ddic.configure('top/*.clk', clk.c['clk'])
    ddic.configure('sim.duration'         , clk.period*duration)
    ddic.provide_on_demand('cls/sim', Simulator, 'sim') # inst_kwargs=dict(log_signal_updates=True, log_event_triggers=True, log_task_switching=True))
    ddic.provide('scheduler', Scheduler())
    inst(TestIseq2Itlm, 'top')
    
    # ddic.configure('sim.log_task_switching', True)
    # ddic.configure('sim.log_event_triggers', True)
    # ddic.configure('sim.log_signal_updates', True)
    
    ddic['sim'].run()


def itlm2iseq_default(gen_num = 1, #random.randint(1, 8),
                      sequence_len = random.randint(1, 10),
                      burst_len = random.randint(1, 10),
                      gen_dtype=bit8):
    
    ddic.configure('top/recv.dtype', Bit(gen_dtype.w*burst_len))
    ddic.configure('top.gen_num', gen_num)
    ddic.configure('top/*.sequence_len', sequence_len)
    ddic.configure('top/*.burst_len', burst_len)

    default_setup_and_run(burst_len*sequence_len+1)
     
    assert len(ddic['top/gen'].samples) == len(ddic['top/recv'].samples)
 
    for i, s in enumerate(ddic['top/recv'].samples):
        gen_val = Bit(0)()
        for k in range(burst_len):
            gen_val = ddic['top/gen'].samples[i][k] % gen_val
        
        assert gen_val == s

def test_itlm2iseq_sequence():
    ddic.configure('top/*.gen_proc', 'sequence_gen')
#    itlm2iseq_default(gen_num = 1, sequence_len = 4, burst_len = 8)
    itlm2iseq_default()

def test_itlm2iseq_array_unroll():
    ddic.configure('top/*.gen_proc', 'array_gen')
    itlm2iseq_default()

test_itlm2iseq_sequence()
