from sydpy import *

class Johnson(Module):
    @arch_def
    def rtl(self, 
    
            clk:sig(bit), 
            dout: 'seq(Bit(N)).master', 
            
            N=1
            ):
            
        dout.data.init(0)
        dout.clk <<= clk
        dout.data <<= dout[N-2:0] % (~dout[N-1]) 
            
class TestJohnson(Module):
    @arch_def
    def dflt(self, cnt_n=1):
        self.inst(Clocking, clk_o='clk', period=10)
        
        self.inst(BasicRndSeq, seq_o='cnt_en', delay=50, init=0, intfs={'seq_o' : tlm(bit).master})
        
        self.inst(Johnson, clk='clk', dout='cnt_out', N=cnt_n)
        
        cnt_out = self.seq(Bit(cnt_n), slave='cnt_out', clk='clk')
        cnt_out.ready <<= 'cnt_en'
        

conf = {
        'sys.top'           : TestJohnson,
        'sys.extensions'    : [VCDTracer],
        '/top.cnt_n'        : 4
        }

Simulator(conf).run()
