from collections import namedtuple
import sydpy

mapping = namedtuple('Mapping', ['m', 'cs', 'slice'])

class JesdPackerAlgo:
    def __init__(self, dtype = None, M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0):
        
        self.N = N
        self.S = S
        self.M = M
        self.CS = CS
        self.CF = CF
        self.F = F
        self.L = L
        self.HD = HD
        self.dtype = dtype
    
    def form_words(self, samples):
        words = []
        if self.CF == 0:
            for s in samples:
                words.append(s[0] % s[1])
        else:
            control_word = self.dtype(0)()
            for s in samples:
                words.append(s[0])
                control_word %= s[1]
            
            words.append(control_word)
        
        return words
    
    def form_nibble_groups(self, words):
        nibble_groups = []
        for w in words:
            ng = []
            upper = len(w)
            while upper >= 4:
                ng.append(w[upper-4:upper-1])
                upper -= 4;
                
            if upper != 0:
                ng.append(w[0:upper-1] % self.dtype(4-upper)(0))
                
            nibble_groups.append(ng)
                
        return nibble_groups
    
    def form_lane_groups(self, ng):
        lg_nibbles = []
        start = 0
        if self.HD == 0:
            start = 0
            for i in range(self.L):
                lane_ng = []
                while (len(lane_ng) < self.F*2) and (start < len(ng)):
                    if len(lane_ng) + len(ng[start]) <= self.F*2:
                        lane_ng.extend(ng[start])
                        start += 1
                    else:
                        break
                    
                for i in range(len(lane_ng), self.F*2):
                    lane_ng.append(self.dtype(4)(0))
                            
                lg_nibbles.append(lane_ng)
        else:
            start = 0
            nibbles = []
            for n in ng:
                nibbles.extend(n)
            
            for i in range(self.L):
                if (start + self.F*2) <= len(nibbles):
                    lane_ng = nibbles[start:start+self.F*2]
                else:
                    lane_ng = nibbles[start:]
                    for i in range(len(lane_ng), self.F*2):
                        lane_ng.append(self.dtype(4)(0))
                
                start += self.F*2       
                lg_nibbles.append(lane_ng)
        
        lg = []
        for l in lg_nibbles:
            lane = []
            for i in range(0,len(l),2):
                lane.append(l[i] % l[i+1])
        
            lg.append(lane)

        return lg
    
    def pack(self, samples):
        words = self.form_words(samples)
        print('Words: ', words)
        ng = self.form_nibble_groups(words)
        print('NG: ', ng)
        frame = self.form_lane_groups(ng)
        
        return frame

def SymbolicBit(w):
    return type('symbit', (SymbolicBitABC,), dict(w=w))

class SymbolicBitABC:
    w = 1
    
    def __init__(self, val=[], vld=None, defval = 0):
        try:
            l = len(val)
        except:
            val = []
            l = 0
            
        self.val = val + [defval]*(self.w - l)
        
    def __mod__(self, other):
        return SymbolicBit(self.w + other.w)(val = other.val + self.val)

    def __len__(self):
        return self.w

    def __str__(self):
        return str(self.val)

    def __repr__(self):
        return repr(self.val)

    def __getitem__(self, key):
        if isinstance( key, slice ) :
            high = max(key.start, key.stop)
            low = min(key.start, key.stop)
        elif isinstance( key, int ) :
            high = low = int(key)
        else:
            raise TypeError("Invalid argument type.")
        
        return SymbolicBit(high-low+1)(val = self.val[low:(high+1)])


def pack_samples(samples, M, CF, CS, F, HD, L, S, N):
    dtype = sydpy.Bit
      
    print('Samples: ', samples_conv)    
    p = PackerTlAlgo(dtype = dtype, M=M, N=N, S=S, CS=CS, CF=CF, L=L, F=F, HD=HD)
    return p.pack(samples)

def calc_pack_matrix(M, CF, CS, F, HD, L, S, N):
    m = [[0]*F for _ in range(L)]
#     dtype = sydpy.Bit
    dtype = SymbolicBit
    
    sym_samples = []
    for i in range(M):
        sym_samples.append((dtype(N)([(i, 0, j) for j in range(N)]), 
                            dtype(CS)([(i, 1, j) for j in range(CS)])))    
    
    print('Samples: ', sym_samples)
    p = PackerTlAlgo(dtype = dtype, M=M, N=N, S=S, CS=CS, CF=CF, L=L, F=F, HD=HD)
    return p.pack(sym_samples)
    
if __name__  == "__main__":
    samples = [(0x660,0x0), (0x189,0x2), (0x000,0x3), (0x0ef,0x0), (0x3cb,0x1), (0x0a0,0x1), (0x53f,0x1), (0x432,0x1), (0x553,0x0), (0x21e,0x2), (0x02a,0x3), (0x38d,0x0), (0x779,0x2), (0x32f,0x2), (0x347,0x0), (0x2d9,0x3)]
    
    samples_conv = []
    for (d, cs) in samples:
        samples_conv.append((sydpy.Bit(11)(d), sydpy.Bit(2)(cs)))
    
    m = calc_pack_matrix(M=16, N=11, S=1, CS=2, CF=1, L=7, F=4, HD=1)
    frame = pack_samples(samples_conv, M=16, N=11, S=1, CS=2, CF=1, L=7, F=4, HD=1)
    
    for f_lane, m_lane in zip(frame, m):
        for f_byte, m_byte in zip(f_lane, m_lane):
            for f_bit, m_bit in zip(f_byte, m_byte.val):
                if m_bit:
                    assert int(f_bit) == samples_conv[m_bit[0]][m_bit[1]][m_bit[2]] 
