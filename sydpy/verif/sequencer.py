'''
Created on Oct 9, 2014

@author: bvukobratovic
'''

from sydpy.intfs import tlm
from sydpy.types._type_base import TypeBase
from sydpy._util._util import fannotate 
from sydpy import Module, architecture

class Sequencer(Module):
    '''
    classdocs
    '''

    def set_seq(self, sequence, **config):
        self.inst(sequence, 'sequence', seq_o=self.seq_o,  **config)

    @architecture
    def dflt(self, seq_o, seq_module=None):
        '''
        Constructor
        '''
        
        self.seq_o = seq_o
        
        if seq_module:
            self.set_seq(seq_module[0], **seq_module[1])
            
# def Sequencer(seq_o_intf):
#      
#     seq_o_intf = tlm(seq_o_intf.dtype)
#      
#     dflt_arch = fannotate(_Sequencer.dflt, seq_o=seq_o_intf)
#      
#     cls = type('BasicRndSeq', (_Sequencer,), dict(dflt=dflt_arch))
#     
#     return cls
        