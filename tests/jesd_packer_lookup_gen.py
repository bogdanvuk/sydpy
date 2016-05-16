from tests.jesd_packer_algo import JesdPackerAlgo

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

def create_lookup(jesd_params, sample_flatten=False):

    dtype = SymbolicBit
    packer_algo = JesdPackerAlgo(dtype=dtype, jesd_params=jesd_params)
    
    sym_samples = []
    for i in range(jesd_params['M']):
        for k in range(jesd_params['S']):
            if sample_flatten:
                sym_samples.append((dtype(jesd_params['N'])([(i, k*(jesd_params['N'] + jesd_params['CS']) + j) for j in range(jesd_params['N'])]), 
                            dtype(jesd_params['CS'])([(i, k*(jesd_params['N'] + jesd_params['CS']) + j + jesd_params['N']) for j in range(jesd_params['CS'])])))
            else:
                sym_samples.append((dtype(jesd_params['N'])([(i, 0, j) for j in range(jesd_params['N'])]), 
                            dtype(jesd_params['CS'])([(i, 1, j) for j in range(jesd_params['CS'])])))    
    
    
    print('Samples: ', sym_samples)
    return packer_algo.pack(sym_samples)
