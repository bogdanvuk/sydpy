import sydpy
from sydpy.types.bit import Bit, bit8
from tests.jesd_packer_lookup_gen import create_lookup, SymbolicBit
from sydpy.types.array import Array

class Jesd32bpLLookupPacker(sydpy.Component):

    def __init__(self, name, frame_out, ch_samples, tSample = None, arch='tlm', jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0), **kwargs):
        sydpy.Component.__init__(self, name)
        self.jesd_params = jesd_params

        frame_lookup = create_lookup(jesd_params, sample_flatten=True)
        self.segments_32b_num = (1 if jesd_params['F'] <= 4 else int(jesd_params['F'] / 4))
        self.overframe_num = (1 if jesd_params['F'] >= 4 else int(4 / jesd_params['F']))
        self.oversample_num = jesd_params['S']*self.overframe_num
        self.input_vector_w = self.oversample_num*(tSample.dtype['d'].w + tSample.dtype['cs'].w)
        self.oversample_per_frame_w = jesd_params['S']*(tSample.dtype['d'].w + tSample.dtype['cs'].w)
        
        self.lookup = []
        for frame_lane in frame_lookup:
            lane = []
            for frame_cnt in range(self.overframe_num):
                for b in frame_lane:
                    b_shift = []
                    for v in b.val:
                        b_shift.append((v[0], v[1] + frame_cnt*self.oversample_per_frame_w)) 
                    lane.append(SymbolicBit(b.w)(b_shift))
                    
            self.lookup.append(lane)
        
        for i in range(2):
            self.inst(sydpy.Isig, 'frame{}'.format(i)) #, dtype=Array(Array(bit8, jesd_params['F']), jesd_params['L']))
        
        self.cur_frame_in = self.frame0
        self.inst(sydpy.Isig, 'segments_32b_cnt', dtype=int)
        self.inst(sydpy.Isig, 'cur_frame_out', dtype=int, dflt=1)
        
        frame_out <<= self.inst(sydpy.Isig, 'frame_out', dtype=Bit(32*jesd_params['L']))
        
        self.idin = []
        for i, d in enumerate(ch_samples):
            idin = self.inst(sydpy.Iseq, 'din{}'.format(i), dtype=Bit(self.input_vector_w), dflt=0)
            if self.segments_32b_num == 1:
                idin.ready <<= True
            else:
                idin.ready <<= False
                
            self.idin.append(idin)
            d >>= idin
            
        self.inst(sydpy.Process, 'pack', self.pack, senslist=[self.din0.clk.e.posedge])
        self.inst(sydpy.Process, 'dispatch', self.dispatch, senslist=[self.din0.clk.e.posedge])

    
    def pack(self):
        
        for intf in self.idin:
            if (self.segments_32b_num > 1) and (self.segments_32b_cnt.read() == self.segments_32b_num - 2):
                intf.ready <<= True
            else:
                intf.ready <<= False
        
        self.segments_32b_cnt <<= self.segments_32b_cnt() + 1
        if self.segments_32b_cnt() == self.segments_32b_num - 1:
            self.segments_32b_cnt <<= 0
            frame = []
            for m_lane in self.lookup:
                f_lane = []
                for m_byte in m_lane:
                    f_byte = sydpy.Bit(8)(0)
                    for i, m_bit in enumerate(m_byte.val):
                        if m_bit:
                            f_byte[i] = self.idin[m_bit[0]].data()[m_bit[1]]
                        else:
                            f_byte[i] = 0
                    f_lane.append(f_byte)
                    
                frame.append(f_lane)
            
            if self.cur_frame_out() == 0:
                self.frame1 <<= frame
                self.cur_frame_out <<= 1
            else:
                self.frame0 <<= frame
                self.cur_frame_out <<= 0
            
            print()
            print('Prepared Frame:')
            print()
            for l in frame:
                print(l)
            
    
    def dispatch(self):

        if self.cur_frame_out() == 0:
            print('frame0 output')
            frame = self.frame0()
        else:
            print('frame1 output')
            frame = self.frame1()        

        out_word = []

        if frame:        
            for l in range(self.jesd_params['L']):
                for i in range(4):
                    out_word.append(frame[l][self.segments_32b_cnt()*4 + i])
                    self.frame_out[l*32+(i+1)*8 - 1:l*32+i*8] <<= frame[l][self.segments_32b_cnt()*4 + i]
                
            print('32bpL out: {}, {}'.format(self.frame_out.read_next(), out_word))
