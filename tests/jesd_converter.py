import sydpy

class Converter(sydpy.Component):
    def __init__(self, name, ch_sample, N, CS, tSample = None):
        super().__init__(name)
        
        self.N = N
        self.CS = CS
        ch_sample <<= self.inst(sydpy.Itlm, 'sample', dtype=tSample, dflt={'d': 0, 'cs':0})

        self.inst(sydpy.Process, 'p_gen', self.gen)
        self.rnd_gen = sydpy.rnd(sydpy.Bit(N + CS))
        
    def gen(self):
        for r in self.rnd_gen:
            data = {'d': r[0:self.N-1], 'cs': r[self.N:self.N+self.CS-1]}
            print('GEN {}: {}'.format(self.name, data))
            self.c['sample'].bpush(data)