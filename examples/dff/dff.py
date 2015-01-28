from sydpy import *

class Dff(Module):
    @arch_def
    def rtl(self, 

            clk: sig(bit), 
            din: sig(bit), 
            dout: sig(bit).master
            ):
        
        @always(self, clk.e.posedge)
        def reg():
            dout.next = din
            
            
class TestDff(Module):
    @arch_def
    def dflt(self):
        self.inst(Clocking, clk_o='clk', period=10)
        
        self.inst(Dff, clk='clk', din='din', dout='dout')
        
        self.inst(BasicRndSeq, seq_o='din', delay=30, intfs={'seq_o' : tlm(bit).master})

conf = {
        'sys.top'           : TestDff,
        'sys.extensions'    : [VCDTracer]
        }

Simulator(conf).run()
