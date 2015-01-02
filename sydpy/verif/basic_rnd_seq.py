#  This file is part of sydpy.
# 
#  Copyright (C) 2014 Bogdan Vukobratovic
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

from sydpy import Module, architecture, always, rnd, simwait, Delay
from .basic_seq import BasicSeq

class BasicRndSeq(BasicSeq):
    '''
    classdocs
    '''
    def rnd_gen(self, dtype, delay=None, seed=None):
        self.rnd_var = rnd(dtype, seed)
        
        while(1):
            next_seq = next(self.rnd_var)
            
            try:
                next_delay = self.rnd_var.rnd_int(delay[0], delay[1])
            except TypeError:
                next_delay = delay
            
            yield (next_seq, next_delay)
    
    @architecture
    def tlm(self, seq_o, delay=None, seed=None, flow_ctrl=None):
        BasicSeq.tlm(self, seq_o, self.rnd_gen(seq_o._get_dtype(), delay, seed), flow_ctrl)
