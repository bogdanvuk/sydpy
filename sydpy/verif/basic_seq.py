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
from sydpy.component import Component
from sydpy.intfs.itlm import Itlm
from ddi.ddi import ddic
from sydpy.process import Process

"""Module implements the basic sequencer module."""

from sydpy._delay import Delay

class BasicSeq(Component):
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
    
    def __init__(self, name, seq_o, gen=None, flow_ctrl=True):
        super().__init__(name)
        self.gen = gen
        self.flow_ctrl = flow_ctrl
        self.seq_o = seq_o
        self.inst(Process, func=self.main)

    def main(self):
        for next_seqi, next_delay in self.gen:
            
            if next_delay:
                ddic['sim'].wait(Delay(next_delay))
            
            if self.flow_ctrl:
                self.seq_o.bpush(next_seqi)
            else:
                self.seq_o.push(next_seqi)
