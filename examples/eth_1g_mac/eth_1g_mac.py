'''
Created on Dec 15, 2014

@author: bvukobratovic
'''

from sydpy import *
from examples.crc32.crc32 import Crc32

import zlib
from sydpy.procs.clk import Clocking

eth_usr_pkt = Struct(
                     ('dest', Vector(6, bit8)),
                     ('src', Vector(6, bit8)),
                     ('len_type', bit16),
                     ('data', Array(bit8, max_size=64))
                     )

eth_gmii_pkt = Struct(
                      ('pream', Vector(7, bit8)),
                      ('start', bit8),
                      ('dest', Vector(6, bit8)),
                      ('src', Vector(6, bit8)),
                      ('len_type', bit16),
                      ('data', Array(bit8, max_size=64)),
                      ('crc', bit32)
                     )


# Found the algorithm at: http://www.hackersdelight.org/hdcodetxt/crc.c.txt
def setup_crc_table():
    crc_table = []
    
    for byte in range(0, 256):
        crc = bit32(byte)
        
        for _ in range(8, 0, -1):
            mask = -(int(crc) & 1)
        
            crc = (crc >> 1) ^ (0xEDB88320 & mask);

        crc_table.append(crc);
        
    return crc_table

preamble_last_pos = 7
sfd_pos = preamble_last_pos + 1
dest_last_pos = sfd_pos + 6
src_last_pos = dest_last_pos + 6
len_type_first_pos = src_last_pos + 1
len_type_second_pos = len_type_first_pos + 1 

class Eth1GMac(Module):
    @arch
    def tlm(self, 
            pkt_in : tlm(eth_usr_pkt),
            pkt_out: tlm(eth_gmii_pkt).master
        ):
        
        @always_acquire(self, pkt_in)
        def proc(pkt):
                     
            if len(pkt.data) < 46:
                pkt.data += [bit8(0) for _ in range(46 - len(pkt.data))]

            crc = 0
            for b in convgen(pkt, bit8):
                crc = zlib.crc32(bytes([int(b)]), crc)
#                 print("{0} -> {1}".format(b, hex(~bit32(crc))))
                
#             print("Final: {0}".format(hex(bit32(crc))))

            crc = zlib.crc32(bytes(map(int, 
                                       convgen(pkt, bit8)
                                       ))
                             )
            crc_rev = list(convgen(bit32(crc), bit8))[::-1]
            
            pkt_gmii = eth_gmii_pkt([
                                     [bit8(0x55) for _ in range(7)],
                                     bit8(0xd5),
                                     pkt.dest,
                                     pkt.src,
                                     pkt.len_type,
                                     pkt.data,
                                     conv(crc_rev, bit32)
                                     ])
            
            pkt_out.next = pkt_gmii
            
#             s = ''
#             
#             print(hex(crc))
# 
#             print(str(conv(crc_rev, bit32)))
#             
#             for b in convgen(pkt_gmii[2:6], bit8):
#                 s += str(b)[2:]
#                 
#             print(s)
#             

    @arch_def
    def rtl(self, 
            clk     : sig(bit), 
            pkt_in  : seq(bit8), 
            pkt_out : seq(bit8).master
            ):
        
        self.inst(Crc32, 
                    clk = clk,
                    crc_in = 'crc_data', 
                    crc_out='crc',
                  )
        
        pkt_in.clk <<= clk
        pkt_out.clk <<= clk
        
        crc_data = self.seq(bit8, 'crc_data', clk=clk, init=0)
        crc = self.seq(bit32, slave='crc', clk=clk)
        
        fsm_states = Enum('idle', 'preamble', 'sfd', 'dest', 'src', 'len_type', 'data', 'pad', 'crc0', 'crc1', 'crc2', 'crc3', 'pkt_end')
        fsm_state = self.seq(fsm_states, 'fsm_state', clk=clk, init='idle')

        len_type = self.seq(bit16, 'len_type', clk=clk)
        
        pkt_cnt = self.sig(bit16, 'pkt_cnt', init=0)
        
        pkt_in.ready <<= (fsm_state == ['idle', 'dest', 'src', 'len_type', 'data'])
        
        pkt_in_last_reg = self.seq(bit, clk=clk)
        pkt_in_last_reg.data <<= pkt_in.last
        
        @always(self, clk.e.posedge)
        def pkt_cnt_proc():
            if fsm_state in ['idle', 'pkt_end']:
                pkt_cnt.next = 1
            else:
                pkt_cnt.next = pkt_cnt + 1
        
        @always_comb(self) #, fsm_state, pkt_in, crc_out)
        def pkt_out_intf():
            if fsm_state in ('idle', 'pkt_end'):
                pkt_out.valid.next = False
            else:
                pkt_out.valid.next = True
                
            if fsm_state == 'idle':
                pkt_out.next = 0
            elif fsm_state == 'preamble':
                pkt_out.next = 0x55
            elif fsm_state == 'sfd':
                pkt_out.next = 0xd5
            elif fsm_state in ('dest', 'src', 'len_type', 'data'):
                pkt_out.next = pkt_in
            elif fsm_state == 'pad':
                pkt_out.next = 0
            elif fsm_state == 'crc3':
                try:
                    pkt_out.next = bit8(crc >> 24)
                except:
                    pkt_out.next = 0xff
            elif fsm_state == 'crc2':
                try:
                    pkt_out.next = bit8(crc >> 16)
                except:
                    pkt_out.next = 0xff
            elif fsm_state == 'crc1':
                try:
                    pkt_out.next = bit8(crc >> 8)
                except:
                    pkt_out.next = 0xff
            elif fsm_state == 'crc0':
                try:
                    pkt_out.next = bit8(crc)
                except:
                    pkt_out.next = 0xff
                
            if fsm_state == 'crc0':
                pkt_out.last.next = True
            else:
                pkt_out.last.next = False
        
        @always_comb(self)
        def fsm_proc():
            
            crc_data.last.next = 0
            
            if fsm_state == 'idle':
                if pkt_in.valid:
                    len_type.next = 0
                    fsm_state.next = 'preamble'
            elif fsm_state == 'preamble':
                if pkt_cnt == preamble_last_pos:
                    fsm_state.next = 'sfd'
            elif fsm_state == 'sfd':
                fsm_state.next = 'dest'
            elif fsm_state == 'dest':
                if pkt_cnt == dest_last_pos:
                    fsm_state.next = 'src'
            elif fsm_state == 'src':
                if pkt_cnt == src_last_pos:
                    fsm_state.next = 'len_type'
            elif fsm_state == 'len_type':
                if pkt_cnt == len_type_first_pos:
                    len_type[7:0].next = pkt_in
                elif pkt_cnt == len_type_second_pos:
                    len_type[15:8].next = pkt_in
                    fsm_state.next = 'data'
            elif fsm_state == 'data':
                if (pkt_cnt == len_type_second_pos + len_type) or \
                    (pkt_in_last_reg and pkt_cnt < 60 + sfd_pos):
                    fsm_state.next = 'pad'
                elif pkt_in_last_reg:
                    fsm_state.next = 'crc3'
                    crc_data.last.next = 1
            elif fsm_state == 'pad':
                if pkt_in_last_reg or pkt_cnt == 60 + sfd_pos:
                    fsm_state.next = 'crc3'
                    crc_data.last.next = 1
            elif fsm_state == 'crc3':
                fsm_state.next = 'crc2'
            elif fsm_state == 'crc2':
                fsm_state.next = 'crc1'
            elif fsm_state == 'crc1':
                fsm_state.next = 'crc0'
            elif fsm_state == 'crc0':
                fsm_state.next = 'pkt_end'
            elif fsm_state == 'pkt_end':
                if pkt_in.valid:
                    fsm_state.next = 'preamble'
                else:
                    fsm_state.next = 'idle'
        
        @always_comb(self)
        def crc_sig_gen():
            if fsm_state == 'pad':
                crc_data.valid.next = 1
                crc_data.data.next = 0
            else:
                crc_data.valid.next = (fsm_state in ['dest', 'src', 'len_type', 'data', 'pad']) 
                crc_data.data.next = pkt_in
            
if __name__ == "__main__":
    
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
            'sys.sim.duration'  : 15000 
            }
    
    sim = Simulator(conf)
    
    sim.run()

