
class JesdPackerAlgo:
    def __init__(self, dtype = None, jesd_params=dict(M=1, N=8, S=1, CS=0, CF=0, L=1, F=1, HD=0)):
        
        for k,v in jesd_params.items():
            setattr(self, k, v)
        
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
