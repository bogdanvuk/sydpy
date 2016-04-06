import sydpy
from tests.packer_coef_calc import JesdPackerAlgo

class PackerTlAlgo(sydpy.Component, JesdPackerAlgo):
    def __init__(self, name, ch_samples, tSample = None, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0, **kwargs):
        sydpy.Component.__init__(self, name)
        JesdPackerAlgo.__init__(self, dtype = sydpy.Bit, M=len(ch_samples), N=N, S=S, CS=CS, CF=CF, L=L, F=F, HD=HD)
        self.csin = []
        self.din = []
        for i, d in enumerate(ch_samples):
            self.din.append(self.inst(sydpy.Itlm, 'din{}'.format(i), dtype=tSample, dflt={'d': 0, 'cs':0}))
            d >>= self.din[-1]
        
        self.inst(sydpy.Itlm, 'frame')
        self.inst(sydpy.Process, 'pack', self.pack)
    
    def pack(self):
        while(1):
            sydpy.ddic['sim'].wait(sydpy.Delay(10))
            samples = []
            for _ in range(self.S):
                for d in self.din:
                    samples.append(d.bpop())
            
            frame = JesdPackerAlgo.pack(self, samples)
            self['frame'].push(frame)
            print()
            print('Algo Output Frame:')
            print()
            for l in frame:
                print(l)
            