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

"""Module implements the basic sequencer module."""

from sydpy import Module, arch_def, always
from sydpy._simulator import simwait
from sydpy._delay import Delay

class BasicSeq(Module):
    """Basic sequence module that sends the transactions created by the 
    supplied generator function.
    
    Example instantiation:
        self.inst(BasicSeq, seq_o, gen, flow_ctrl, intfs={'seq_o' : tlm(bit).master})
        
    seq_o      - The output interface

    gen        - The supplied generator function should return two values:
    
            next_seqi     - The transaction that should be written to channel
            next_delay    - The delay before writing the transaction.

    flow_ctrl  - Can have the following values:
            True     - Transaction is not sent until the channel is empty
            False    - Transaction is sent regardless of the channel
            
    intfs      - Declares the interface type of the output. Interface has to be a subclass
            of tlm and it has to be master.
    """
    
    @arch_def
    def tlm(self, seq_o, gen=None, flow_ctrl=True):

        @always(self)
        def main():
            for next_seqi, next_delay in gen:
                
                if next_delay:
                    simwait(Delay(next_delay))
                
                if flow_ctrl:
                    seq_o.blk_next = next_seqi
                else:
                    seq_o.next = next_seqi
