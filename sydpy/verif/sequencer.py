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

"""Module implements the sequencer."""

from sydpy import Module, arch_def

class Sequencer(Module):

    def set_seq(self, sequence, **config):
        self.inst(sequence, 'sequence', seq_o=self.seq_o,  **config)

    @arch_def
    def dflt(self, seq_o, seq_module=None):
        
        self.seq_o = seq_o
        
        if seq_module:
            self.set_seq(seq_module[0], **seq_module[1])
        