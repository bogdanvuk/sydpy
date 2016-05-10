import sydpy
from tests.jesd_packer_algo import JesdPackerAlgo

class PackerTlAlgo(sydpy.Component):
    def __init__(self, name, ch_samples, tSample = None, jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0), **kwargs):
        sydpy.Component.__init__(self, name)
        self.jesd_params = jesd_params
        self.packer = JesdPackerAlgo(dtype = sydpy.Bit, jesd_params=jesd_params)

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
            for _ in range(self.jesd_params['S']):
                for d in self.din:
                    samples.append(d.bpop())
            
            frame = self.packer.pack(samples)
            self.c['frame'].push(frame)
            print()
            print('Algo Output Frame:')
            print()
            for l in frame:
                print(l)
            