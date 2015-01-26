#  This file is part of sydpy.
# 
#  Copyright (C) 2014-2015 Bogdan Vukobratovic
#
#  sydpy is free software: you can redistribute it and/or modify 
#  it under the terms of the GNU Lesser General Public License as 
#  published by the Free Software Foundation, either version 2.1 
#  of the License, or (at your option) any later version.
# 
#  sydpy is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Lesser General Public License for more details.
# 
#  You should have received a copy of the GNU Lesser General 
#  Public License along with sydpy.  If not, see 
#  <http://www.gnu.org/licenses/>.

"""Module implements random generator for sydpy types."""

import sys
import random

class rnd(object):
    '''
    classdocs
    '''
    
    def __init__(self, dtype, seed=None):
        self.dtype = dtype
        
        if seed is None:
            self.set_seed(seed)
        else:
            self.randomize()

    def set_seed(self, seed):
        self.seed = seed
        self.rnd_gen = random.Random(seed)
    
    def randomize(self):
        self.set_seed(int(random.SystemRandom(0).random() * 65536))      
    
    def rnd_int(self, imin=0, imax=sys.maxsize):
        return self._rnd_int(imin, imax)
    
    def _rnd_int(self, imin=0, imax=sys.maxsize):
        return self.rnd_gen.randint(imin, imax)
    
    def _rnd(self, dtype):
        try:
            return getattr(self, "_rnd_" + dtype.__class__.__name__)()
        except AttributeError:
            pass
        
        try:
            return getattr(self, "_rnd_" + dtype.__name__)()
        except AttributeError:
            pass
        
        return dtype._rnd(self)
        
    def __next__(self):
        return self._rnd(self.dtype)
        
        
