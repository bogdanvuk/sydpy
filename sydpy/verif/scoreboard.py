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
from sydpy.intfs.itlm import Itlm
from sydpy.process import Process
from ddi.ddi import ddic

"""Module implements the basic scoreboard module."""

from sydpy import Component

class Scoreboard(Component):
    """Basic scoreboard class that listens with two TLM interfaces and compares 
    the received transactions."""

    def __init__(self, name, intfs = [], dtype=None):
        super().__init__(name)
        
        self.scoreboard_results = {
                    'intfs': intfs,
                    'fail': [],
                    'results' : []
                   }
        
        self.recv_intfs = []
        self.intfs = intfs
        
        if dtype is None:
            dtype = intfs[0]._get_dtype()
        
        for i, intf in enumerate(intfs):
            self.recv_intfs.append(self.inst(Itlm, str(i), dtype=dtype))
            self.recv_intfs[-1] << intf
        
        self.recv_data = [[] for _ in range(len(intfs))]
        
        self.inst(Process, 'dflt', self.dflt, 
                  senslist= [i.e.enqueued for i in self.recv_intfs]
                  )

    def compare(self, ref_trans, dut_trans):
        return (ref_trans == dut_trans)

    def dflt(self): #dut_i, ref_i, dut_name=None, ref_name=None, dut_active=True, ref_active=True, verbose=False):
        for i, intf in enumerate(self.recv_intfs):
            while not intf.empty():
                self.recv_data[i].append(intf.pop())
        
        print('Scoreboard {} and {} @ {}: {}'.format(self.intfs[0].name, self.intfs[1].name, ddic['sim'].time, self.recv_data))
        
        for _ in range(min(map(len, self.recv_data))):
            vals = []
            for i in range(len(self.recv_intfs)):
                vals.append(self.recv_data[i].pop(0))
                
            score = None
            for v in vals[1:]:
                score = self.compare(v, vals[0])
                if not score:
                    break
                
            score = {
                 'trans': [str(v) for v in vals],
                 'time' : ddic['sim'].time,
                 'score': score
                 }
            
            if not score['score']:
                self.scoreboard_results['fail'].append(score)
            
            self.scoreboard_results['results'].append(score)
                     
            pass
#             if ref_active:
#                 ref_trans = ref_i.blk_pop()
#             else:
#                 ref_trans = ref_i.read()
#                 
#             if dut_active:
#                 dut_trans = dut_i.blk_pop()
#             else:
#                 dut_trans = dut_i.read()
#             
#             score = {
#                      'ref_trans': str(ref_trans),
#                      'dut_trans': str(dut_trans),
#                      'score':   self.compare(ref_trans, dut_trans)
#                      }
#             
#             if score['score'] == False:
#                 self.scoreboard_results['fail'].append(len(self.scoreboard_results['results']))
#             
#             if verbose:
#                 print(ref_trans)
#                 print(dut_trans)
#                 print(score['score'])
#             
#             self.scoreboard_results['results'].append(score)
#                 
                