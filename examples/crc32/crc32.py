from sydpy import *
import zlib

# Algorithm from: http://www.hackersdelight.org/hdcodetxt/crc.c.txt
def setup_crc_table():
    crc_table = []
    
    for byte in range(0, 256):
        crc = bit32(byte)
        
        for _ in range(8, 0, -1):
            mask = -(int(crc) & 1)
        
            crc = (crc >> 1) ^ (0xEDB88320 & mask);

        crc_table.append(crc);
        
    return crc_table

class Crc32(Module):
    @arch
    def tlm(self, crc_in: tlm(Array(bit8)).slave, crc_out: tlm(bit32).master):
        @always_acquire(self, crc_in)
        def proc(val):
            crc = 0
            for b in val:
                crc = zlib.crc32(bytes([int(b)]), crc)
                  
            crc_out.blk_next = crc
    
        
    # Algorithm from: http://www.hackersdelight.org/hdcodetxt/crc.c.txt
    @arch_def
    def rtl(self, clk: sig(bit), crc_in: seq(bit8), crc_out: seq(bit32).master):
        
        crc_table = setup_crc_table()
        
        crc_in.clk <<= clk
        
        crc_states = Enum('idle', 'conv')
        crc_state = self.seq(crc_states, master='crc_state', init='idle', clk=clk)
        
        crc_calc = self.seq(bit32, 'crc_calc', init=0xffffffff, clk=clk)
        crc_calc.s_con(**subintfs(crc_in, ['valid', 'last']))

        @always_comb(self)
        def crc_state_proc():
            if crc_in.last:
                crc_state.next = 'idle'
            elif crc_in.valid:
                crc_state.next = 'conv'
        
        @always_comb(self)
        def crc_calc_proc():
            if crc_in.valid:
                if crc_state == 'idle':
                    crc_calc.data.next = (0xffffffff >> 8) ^ crc_table[(0xffffffff ^ crc_in.data) & 0xFF];
                else:
                    crc_calc.data.next = (crc_calc >> 8) ^ crc_table[(crc_calc ^ crc_in.data) & 0xFF]
        
        crc_out.s_con(valid = crc_calc.last, 
                      data  = ~crc_calc.data,
                      )
        crc_out.clk <<= clk
        
if __name__ == "__main__":
    
    class TestCrc32(Module):
        @arch_def
        def dflt(self):
            self.inst(Clocking, clk_o='clk', period=10)
            
            self.inst(Crc32, 
                        clk = 'clk',
                        crc_in = 'crc_data', 
                        crc_out='crc',
                      
                        arch=['rtl', 'tlm'],
                        scrbrd=(Scoreboard, {'intfs': {'dut_i': tlm(bit32).slave, 'ref_i': tlm(bit32).slave}})
                      )
            
            self.inst(BasicRndSeq, seq_o='crc_data', delay=(0, 150), intfs={'seq_o' : tlm(Array(bit8, 10)).master})
    
    conf = {
            'sys.top'           : TestCrc32,
            'sys.extensions'    : [VCDTracer, SimtimeProgress],
            }
    
    for t in UnitTest([(conf, 'crc32')], verbose=True):
        assert bool(t) == True
