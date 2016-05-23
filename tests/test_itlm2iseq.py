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
    def __init__(self, name, chout, gen_proc='array_gen', dtype=bit8, sequence_len=1, burst_len=1):
        super().__init__(name)
        
        chout <<= self.inst(Itlm, 'dout', dtype=dtype if gen_proc == 'sequence_gen' else Array(dtype))
        self.inst(Process, 'p_gen', getattr(self, gen_proc))
        self.rnd_gen = rnd(dtype)
        self.samples = [] 
        self.burst_len = burst_len
        self.sequence_len = sequence_len
        self.dtype = dtype
        
    def sequence_gen(self):
        while len(self.samples) < self.sequence_len:
            for i, r in enumerate(itertools.islice(self.rnd_gen, 0, self.burst_len)):
                if i == 0:
                    self.samples.append([])
                    self.dout.bpush(r)
                    self.samples[-1].append(r)
                else:
                    self.dout.push(r)
                    self.samples[-1].append(r)

    def array_gen(self):
        while len(self.samples) < self.sequence_len:
            dout = Array(self.dtype)(list(itertools.islice(self.rnd_gen, 0, self.burst_len)))
            self.samples.append(dout)
            self.dout.bpush(dout)
                
class Receiver(Component):
    def __init__(self, name, chin, dtype=bit8):
        super().__init__(name)
        
        din = self.inst(Iseq, 'din', dtype=dtype)
        slice_size = int(dtype.w / len(chin))
        for i, ch in enumerate(chin):
            ch >>= din[i*slice_size: (i+1)*slice_size - 1]
            
        self.inst(Process, 'proc', func=self.proc, senslist=[self.din.clk.e.posedge])
        self.samples = []
        self.transaction_done = True
        
    def proc(self):
        if self.din.valid():
            if self.transaction_done:
                self.samples.append([])
                self.transaction_done = False
            
            self.samples[-1].append(self.din.data())
            
            if self.din.last():
                self.transaction_done = True
        
class TestIseq2Itlm(Component):
    def __init__ (self, name, gen_num=1):
        super().__init__(name)
        
        chin=[]
        for i in range(gen_num):
            ch = self.inst(Channel, 'ch_gen{}'.format(i))
            self.inst(Generator, 'gen{}'.format(i), chout=ch)
            chin.append(ch)
            
        self.inst(Receiver, 'recv', chin=chin)

def teardown_function(function):
    ddic.clear()

def default_setup_and_run(duration):
    clk = inst(Clocking, 'clocking')
    ddic.configure('top/*.clk', clk.c['clk'])
    ddic.configure('sim.duration'         , clk.period*duration)
    inst(TestIseq2Itlm, 'top')
    
    # ddic.configure('sim.log_task_switching', True)
    # ddic.configure('sim.log_event_triggers', True)
    # ddic.configure('sim.log_signal_updates', True)
    
    ddic.provide_on_demand('cls/sim', Simulator, 'sim') # inst_kwargs=dict(log_signal_updates=True, log_event_triggers=True, log_task_switching=True))
    ddic.provide('scheduler', Scheduler())
    
    ddic['sim'].run()


def itlm2iseq_default(gen_num = random.randint(1, 8),
                      sequence_len = random.randint(1, 10),
                      burst_len = random.randint(1, 10),
                      gen_dtype=bit8):
    
    ddic.configure('top/recv.dtype', Bit(gen_dtype.w*gen_num))
    ddic.configure('top.gen_num', gen_num)
    ddic.configure('top/*.sequence_len', sequence_len)
    ddic.configure('top/*.burst_len', burst_len)

    default_setup_and_run(burst_len*sequence_len+1)
    
    samples_num = len(ddic['top/recv'].samples)
    
    for i in range(gen_num):
        assert len(ddic['top/gen{}'.format(i)].samples) == samples_num

    for i, s in enumerate(ddic['top/recv'].samples):
        for k in range(burst_len):
            gen_val = Bit(0)()
            for j in range(gen_num):
                gen_val = ddic['top/gen{}'.format(j)].samples[i][k] % gen_val
            
            assert gen_val == s[k]

def test_itlm2iseq_sequence():
    ddic.configure('top/*.gen_proc', 'sequence_gen')
#    itlm2iseq_default(gen_num = 1, sequence_len = 4, burst_len = 8)
    itlm2iseq_default()

def test_itlm2iseq_array_unroll():
    ddic.configure('top/*.gen_proc', 'array_gen')
    itlm2iseq_default()

#test_itlm2iseq_sequence()
