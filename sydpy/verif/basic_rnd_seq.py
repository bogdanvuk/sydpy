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

"""Module implements the basic random sequencer module."""

from sydpy import arch_def, rnd
from .basic_seq import BasicSeq

class BasicRndSeq(BasicSeq):
    """Basic random sequence module that sends the transactions created by the 
    random generator.
    
    Example instantiation:
        self.inst(BasicRndSeq, seq_o, delay=None, seed=None, init=None, intfs={'seq_o' : tlm(bit).master})
        
    seq_o      - The output interface

    delay      - Delay can be either:
            Tuple    - Then it specifies the range from which a random delay is generated
            Integer  - Then it specifies a fixed delay between the transactions
            
    seed       - The seed from random number generation 
    
    init       - Initial value to output, before the first random value is outputted.
            
    intfs      - Declares the interface type of the output. Interface has to be a subclass
            of tlm and it has to be master.
    """
    
    def rnd_gen(self, dtype, delay=None, seed=None, init=None):
        """The generator function to be supplied to BasicSeq to generate the 
        transactions."""
    
        if init is not None:
            yield (init, 0)
        
        self.rnd_var = rnd(dtype, seed)
        
        while(1):
            next_seq = next(self.rnd_var)
            
            try:
                next_delay = self.rnd_var.rnd_int(delay[0], delay[1])
            except TypeError:
                next_delay = delay
            
            yield (next_seq, next_delay)
    
    @arch_def
    def tlm(self, seq_o, delay=None, seed=None, flow_ctrl=True, init=None):
        BasicSeq.tlm(self, seq_o, self.rnd_gen(seq_o, delay, seed, init), flow_ctrl)
