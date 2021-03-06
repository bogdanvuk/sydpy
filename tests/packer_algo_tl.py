import sydpy
from tests.packer_coef_calc import JesdPackerAlgo

class PackerTlAlgo(sydpy.Component, JesdPackerAlgo):
    @sydpy.compinit
    def __init__(self, name, parent, ch_samples, tSample = None, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0, **kwargs):
        sydpy.Component.__init__(self, name, parent)
        JesdPackerAlgo.__init__(self, dtype = sydpy.Bit, M=len(ch_samples), N=N, S=S, CS=CS, CF=CF, L=L, F=F, HD=HD)
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
            
            JesdPackerAlgo.pack(self, samples)
            