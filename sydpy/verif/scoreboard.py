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

from sydpy.intfs import tlm
from sydpy.types._type_base import TypeBase
from sydpy._util._util import fannotate 
from sydpy import Module, architecture, always

class Scoreboard(Module):
    '''
    classdocs
    '''

    def compare(self, ref_trans, dut_trans):
        return (ref_trans == dut_trans)

    @architecture
    def dflt(self, dut_i, ref_i, dut_name=None, ref_name=None, dut_active=True, ref_active=True):
        
        self.scoreboard_results = {
                            'ref_name': ref_name,
                            'dut_name': dut_name,
                            'ref_s': ref_i._fullname,
                            'dut_s': dut_i._fullname,
                            'fail': [],
                            'results' : []
                           }
        
        @always(self)
        def compare():
            while 1:
                if ref_active:
                    ref_trans = ref_i.blk_pop()
                else:
                    ref_trans = ref_i.read()
                    
                if dut_active:
                    dut_trans = dut_i.blk_pop()
                else:
                    dut_trans = dut_i.read()
                
                score = {
                         'ref_trans': str(ref_trans),
                         'dut_trans': str(dut_trans),
                         'score':   self.compare(ref_trans, dut_trans)
                         }
                
                if score['score'] == False:
                    self.scoreboard_results['fail'].append(len(self.scoreboard_results['results']))
                
#                 print(ref_trans)
#                 print(dut_trans)
#                 print(score['score'])
                
                self.scoreboard_results['results'].append(score)
                
                