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

from sydpy import Module, architecture, always, rnd

class BasicSeq(Module):
    @architecture
    def tlm(self, seq_o, gen=None, flow_ctrl=None):
        
        @always(self)
        def main():
            for next_seqi, next_delay in gen:
                
                if next_delay:
                    seq_o.next_after = next_seqi, next_delay
                else:
                    seq_o.blk_next = next_seqi
                    