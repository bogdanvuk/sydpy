import sydpy
from tests.packer_coef_calc import JesdPackerAlgo

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

class PackerTlMatrix(sydpy.Component, JesdPackerAlgo):
    @sydpy.compinit
    def __init__(self, name, parent, ch_samples, tSample = None, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0, **kwargs):
        sydpy.Component.__init__(self, name, parent)
        dtype = SymbolicBit
        M = len(ch_samples)
        JesdPackerAlgo.__init__(self, dtype=dtype, M=M, N=N, S=S, CS=CS, CF=CF, L=L, F=F, HD=HD)
    
        sym_samples = []
        for i in range(M):
            sym_samples.append((dtype(N)([(i, 0, j) for j in range(N)]), 
                            dtype(CS)([(i, 1, j) for j in range(CS)])))    
    
        print('Samples: ', sym_samples)
        self.pack_m = JesdPackerAlgo.pack(self, sym_samples)
        
        self.csin = []
        self.din = []
        for i, d in enumerate(ch_samples):
            self.din.append(sydpy.isig('din{}'.format(i), self, dtype=tSample, dflt={'d': 0, 'cs':0}))
            d >>= self.din[-1]
        
        sydpy.Process('pack', self, self.pack)
    
    def pack(self):
        while(1):
            sydpy.ddic['sim'].wait(sydpy.Delay(10))
            samples = []
            for _ in range(self.S):
                for d in self.din:
                    samples.append(d.bpop())
            
            frame = []
            for m_lane in self.pack_m:
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
                
            print(f_lane)
