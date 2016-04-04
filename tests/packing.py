import sydpy

class Converter(sydpy.Component):
    @sydpy.compinit
    def __init__(self, name, parent, ch_sample, tSample = None):
        super().__init__(name, parent)
        
        self.N = N
        self.CS = CS
        ch_sample <<= sydpy.isig('sample', self, dtype=tSample, dflt={'d': 0, 'cs':0})

        sydpy.Process('p_gen', self, self.gen)
        self.rnd_gen = sydpy.rnd(sydpy.Bit(N + CS))
        
    def gen(self):
        for r in self.rnd_gen:
            self['sample'].bpush({'d': r[0:self.N-1], 'cs': r[self.N:self.N+self.CS-1]})
            
class Packer(sydpy.Component):
    @sydpy.compinit
    def __init__(self, name, parent, ch_samples, tSample = None, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0, **kwargs):
        
        self.N = N
        self.S = S
        self.M = len(ch_samples)
        self.csin = []
        self.din = []
        self.CS = CS
        self.CF = CF
        self.F = F
        self.L = L
        self.HD = HD
        for i, d in enumerate(ch_samples):
            self.din.append(sydpy.isig('din{}'.format(i), self, dtype=tSample, dflt={'d': 0, 'cs':0}))
            d >>= self.din[-1]
        
        sydpy.Process('pack', self, self.pack)
    
    def form_words(self, samples):
        words = []
        if self.CF == 0:
            for s in samples:
                words.append(s[0] % s[1])
        else:
            control_word = sydpy.Bit(0)()
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
                ng.append(w[0:upper-1] % sydpy.Bit(4-upper)(0))
                
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
                    lane_ng.append(Bit(4)(0))
                            
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
                    for i in range(len(lange_ng), self.F*2):
                        lane_ng.append(Bit(4)(0))
                
                start += self.F*2       
                lg_nibbles.append(lane_ng)
        
        lg = []
        for l in lg_nibbles:
            lane = []
            for i in range(0,len(l),2):
                lane.append(l[i] % l[i+1])
        
            lg.append(lane)

        return lg
    
    def pack(self):
        while(1):
            sydpy.ddic['sim'].wait(sydpy.Delay(10))
            samples = []
            for _ in range(self.S):
                cs = None
                for d in self.din:
                    samples.append(d.bpop())
#                     if self.CS:
#                         cs = cs.bpop()
#                     samples.append((data, cs))
            
            print(samples)
            
            words = self.form_words(samples)
            print(words)
            ng = self.form_nibble_groups(words)
            print(ng)
            frame = self.form_lane_groups(ng)
            
            print()
            print('Output Frame:')
            print()
            for l in frame:
                print(l)
            

class JesdPacking(sydpy.Component):
    @sydpy.compinit
    def __init__ (self, name, parent, M=1, **kwargs):
        super().__init__(name, parent)
#         for ch in ['ch_gen', 'ch_ping', 'ch_pong']:
#             self.inst(ch, Channel)
        
        ch_gen = []
        for i in range(M):
            ch_gen.append(sydpy.Channel('ch_gen{}'.format(i), self))
            Converter('conv{}'.format(i), self, ch_sample=ch_gen[-1])
            
        Packer('pack', self, ch_samples=ch_gen)

N = 11
CS = 2

conf = [
        ('top.M'       , 16),
        ('top/*.CF'    , 1),
        ('top/*.CS'    , CS),
        ('top/*.F'     , 4),
        ('top/*.HD'    , 1),
        ('top/*.L'     , 7),
        ('top/*.S'     , 1),
        ('top/*.N'     , N),
        ('sim.duration', 10)
        ]

sydpy.ddic.configure('top/*.tSample', sydpy.Struct(('d', sydpy.Bit(N)), 
                                             ('cs', sydpy.Bit(CS))))


for c, v in conf:
    sydpy.ddic.configure(c, v)

sydpy.ddic.provide_on_demand('cls/sim', sydpy.Simulator, 'sim')
sydpy.ddic.provide('scheduler', sydpy.Scheduler())
JesdPacking('top', None)
sydpy.ddic['sim'].run()
