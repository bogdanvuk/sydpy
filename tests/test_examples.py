'''
Created on Dec 25, 2014

@author: bvukobratovic
'''

from sydpy import *
from examples.crc32.crc32 import Crc32
from examples.eth_1g_mac.eth_1g_mac import eth_usr_pkt, Eth1GMac

def test_crc32():
    
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
            'sys.extensions'    : [VCDTracer],
            'sys.duration'      : 5000
            }
    
    for t in UnitTest([(conf, 'crc32')]):
        assert bool(t) == True


def test_eth_1g_mac():
    
    class TestDFF(Module):
        @arch_def
        def test1(self):
            
            self.inst(Clocking, clk_o='clk', period=10)
            
            self.inst(BasicRndSeq, seq_o='usr_pkt', intfs={'seq_o' : tlm(eth_usr_pkt).master})
            
            self.inst(Eth1GMac, 
                      
                      clk='clk', 
                      pkt_in='usr_pkt', 
                      pkt_out='gmii_pkt', 
                            
                      arch=['rtl', 'tlm'],
                      scrbrd=(Scoreboard, {'intfs': {'dut_i': tlm(Array(bit8)), 'ref_i': tlm(Array(bit8))}})
                      )
    
    conf = {
            'sys.top'           : TestDFF,
            'sys.extensions'    : [VCDTracer, SimtimeProgress],
            'sys.sim.duration'  : 7000 
            }
    
    for t in UnitTest([(conf, 'eth_1g_mac')]):
        assert bool(t) == True
     
