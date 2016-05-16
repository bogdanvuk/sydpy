import sydpy
from sydpy.types.bit import Bit
from tests.jesd_packer_lookup_gen import create_lookup

class PackerTlMatrix(sydpy.Component):

    def __init__(self, name, ch_samples, tSample = None, arch='tlm', jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0), **kwargs):
        sydpy.Component.__init__(self, name)
        self.jesd_params = jesd_params
            
        if arch == 'tlm':        
            self.lookup = create_lookup(jesd_params)
            self.csin = []
            self.din = []
            for i, d in enumerate(ch_samples):
                self.din.append(self.inst(sydpy.Itlm, 'din{}'.format(i), dtype=tSample, dflt={'d': 0, 'cs':0}))
                d >>= self.din[-1]
            
            self.inst(sydpy.Itlm, 'frame')
            self.inst(sydpy.Process, 'pack', self.pack)
        elif arch == 'seq':
            self.lookup = create_lookup(jesd_params, sample_flatten=True)
            self.inst(sydpy.Iseq, 'frame')
            self.c['frame'].c['valid'] <<= False
            self.inst(sydpy.Process, 'pack_seq', self.pack_seq, senslist=[self.c['frame'].c['clk'].e['posedge']])
            self.idin = []
            for i, d in enumerate(ch_samples):
                idin = self.inst(sydpy.Iseq, 'din{}'.format(i), dtype=Bit(tSample.dtype['d'].w + tSample.dtype['cs'].w), dflt=0, clk=self.c['frame'].c['clk'])
                self.idin.append(idin)
                d >>= self.c['din{}'.format(i)]
    
    def pack_seq(self):
        
        frame = []
        for m_lane in self.lookup:
            f_lane = []
            for m_byte in m_lane:
                f_byte = sydpy.Bit(8)(0)
                for i, m_bit in enumerate(m_byte.val):
                    if m_bit:
                        f_byte[i] = self.idin[m_bit[0]].c['data'][m_bit[1]]
                    else:
                        f_byte[i] = 0
                f_lane.append(f_byte)
                
            frame.append(f_lane)
        
        self.c['frame'].c['valid'] <<= True
        self.c['frame'] <<= frame
        
        print()
        print('Matrix Output Frame:')
        print()
        for l in frame:
            print(l)
    
    def pack(self):
        while(1):
            sydpy.ddic['sim'].wait(sydpy.Delay(10))
            samples = []
            for _ in range(self.jesd_params['S']):
                for d in self.din:
                    samples.append(d.bpop())
            
            frame = []
            for m_lane in self.lookup:
                f_lane = []
                for m_byte in m_lane:
                    f_byte = sydpy.Bit(8)(0)
                    for i, m_bit in enumerate(m_byte.val):
                        if m_bit:
                            f_byte[i] = samples[m_bit[0]][m_bit[1]][m_bit[2]]
                        else:
                            f_byte[i] = 0
                    f_lane.append(f_byte)
                    
                frame.append(f_lane)
                
            self.c['frame'].push(frame)
                
            print()
            print('Matrix Output Frame:')
            print()
            for l in frame:
                print(l)
