from sydpy import *
from sydpy.extens import VCDTracer, SimtimeProgress

class A(object):
    def read(self):
        print("In A")

class B(object):
    intf = None
    
    def set_intf(self, intf):
        self.intf = intf
        
        self.read = self.intf.read
    
    def read(self):
        print("In B")
        
a = A()
b = B()

b.read()

b.set_intf(a)
b.read()

import sys
sys.exit()

class Dff(Module):
    @architecture
    def rtl(self, clk, din: seq(bit), dout):
        din.clk = clk
        dout <<= din
            
class TestDff(Module):
    @architecture
    def dflt(self):
        self.inst(Clocking, clk_o='clk', period=10)
        
        self.inst(Dff, clk='clk', din='din_seq', dout='dout')
        
        self.inst(BasicRndSeq, seq_o='din_seq', delay=30, intfs={'seq_o' : tlm(bit)})
        

conf = {
        'sys.top'           : TestDff,
        'sys.extensions'    : [VCDTracer, SimtimeProgress],
#         'sys.scheduler.log_task_switching' : True
        }

Simulator(conf).run()
