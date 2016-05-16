from sydpy.component import Component, inst
from sydpy.intfs.isig import Isig
from sydpy._delay import Delay
from sydpy.process import Process
from sydpy.types.bit import bit8, bit16
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
                    self.c['dout'].bpush(r)
                    self.samples[-1].append(r)
                else:
                    self.c['dout'].push(r)
                    self.samples[-1].append(r)

    def array_gen(self):
        while len(self.samples) < self.sequence_len:
            dout = Array(self.dtype)(list(itertools.islice(self.rnd_gen, 0, self.burst_len)))
            self.samples.append(dout)
            self.c['dout'].bpush(dout)
                
class Receiver(Component):
    def __init__(self, name, chin, dtype=bit8):
        super().__init__(name)
        
        din = self.inst(Iseq, 'din', dtype=dtype)
        slice_size = int(dtype.w / len(chin))
        for i, ch in enumerate(chin):
            ch >>= din[i*slice_size: (i+1)*slice_size - 1]
            
        self.inst(Process, 'proc', func=self.proc, senslist=[self.c['din'].c['clk'].e['posedge']])
        self.samples = []
        self.transaction_done = True
        
    def proc(self):
        if self.c['din'].c['valid'].val:
            if self.transaction_done:
                self.samples.append([])
                self.transaction_done = False
            
            self.samples[-1].append(self.c['din'].c['data'].val)
            
            if self.c['din'].c['last'].val:
                self.transaction_done = True
        
class TestIseq2Itlm(Component):
    def __init__ (self, name, gen_cnt=1):
        super().__init__(name)
        
        chin=[]
        for i in range(gen_cnt):
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


def itlm2iseq_default(sequence_len = random.randint(1, 10),
                      burst_len = random.randint(1, 10)):
    ddic.configure('top/*.sequence_len', sequence_len)
    ddic.configure('top/*.burst_len', burst_len)

    default_setup_and_run(burst_len*sequence_len+1)
    
    assert len(ddic['top/gen'].samples) == len(ddic['top/recv'].samples)
    for g, r in zip(ddic['top/gen'].samples, ddic['top/recv'].samples):
        assert g==r
    

# def test_itlm2iseq_sequence():
#     ddic.configure('top/*.gen_proc', 'sequence_gen')
#     itlm2iseq_default()

def test_itlm2iseq_array_unroll():
    ddic.configure('top.gen_cnt', 2)
    ddic.configure('top/recv.dtype', bit16)
    ddic.configure('top/*.gen_proc', 'array_gen')
    itlm2iseq_default(sequence_len=2, burst_len=4)

test_itlm2iseq_array_unroll()

pass