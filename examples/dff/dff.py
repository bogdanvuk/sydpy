from sydpy import *
from sydpy.extens import VCDTracer, SimtimeProgress

class Dff(Module):
    @architecture
    def rtl(self, clk, din: sig(bit), dout):
        
        @always(self, clk.e.posedge)
        def reg():
            dout.next = din
            
            
class TestDff(Module):
    @architecture
    def dflt(self):
        self.inst(Clocking, clk_o='clk', period=10)
        
        self.inst(Dff, clk='clk', din='din_seq', dout='dout')
        
        self.inst(BasicRndSeq, seq_o='din_seq', delay=30, intfs={'seq_o' : tlm(bit)})
        

conf = {
        'sys.top'           : TestDff,
        'sys.extensions'    : [VCDTracer, SimtimeProgress],
        }

sim = Simulator(conf)

sim.run()
