import sydpy
from sydpy.types.bit import Bit
from tests.jesd_packer_lookup_gen import create_lookup, SymbolicBit

class Jesd32bpLLookupPacker(sydpy.Component):

    def __init__(self, name, ch_samples, tSample = None, arch='tlm', jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0), **kwargs):
        sydpy.Component.__init__(self, name)
        self.jesd_params = jesd_params

        frame_lookup = create_lookup(jesd_params, sample_flatten=True)
        self.overframe_cnt = (1 if jesd_params['F'] >= 4 else int(4 / jesd_params['F']))
        self.oversample_cnt = jesd_params['S']*self.overframe_cnt
        self.input_vector_w = self.oversample_cnt*(tSample.dtype['d'].w + tSample.dtype['cs'].w)
        self.oversample_per_frame_w = jesd_params['S']*(tSample.dtype['d'].w + tSample.dtype['cs'].w)
        
        self.lookup = []
        for frame_lane in frame_lookup:
            lane = []
            for frame_cnt in range(self.overframe_cnt):
                for b in frame_lane:
                    b_shift = []
                    for v in b.val:
                        b_shift.append((v[0], v[1] + frame_cnt*self.oversample_per_frame_w)) 
                    lane.append(SymbolicBit(b.w)(b_shift))
                    
            self.lookup.append(lane)
        
        self.inst(sydpy.Iseq, 'frame')
        self.c['frame'].c['valid'] <<= False
        self.inst(sydpy.Process, 'pack', self.pack, senslist=[self.c['frame'].c['clk'].e['posedge']])
        self.idin = []
        for i, d in enumerate(ch_samples):
            idin = self.inst(sydpy.Iseq, 'din{}'.format(i), dtype=Bit(self.input_vector_w), dflt=0, clk=self.c['frame'].c['clk'])
            self.idin.append(idin)
            d >>= idin
    
    def pack(self):
        
        frame = []
        for m_lane in self.lookup:
            f_lane = []
            for m_byte in m_lane:
                f_byte = sydpy.Bit(8)(0)
                for i, m_bit in enumerate(m_byte.val):
                    if m_bit:
                        f_byte[i] = self.idin[m_bit[0]].c['data'].read()[m_bit[1]]
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
