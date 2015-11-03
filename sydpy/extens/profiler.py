'''
Created on Oct 17, 2014

@author: bvukobratovic
'''

import GreenletProfiler
import os
from sydpy.component import Component, compinit, sydsys

class Profiler(Component):

    def coverage_done(self, sim):
        GreenletProfiler.stop()
        stats = GreenletProfiler.get_func_stats()
        stats.print_all(filter_in=['*sydpy*'])
        stats.save(self.out_path + '/profile.callgrind', type='callgrind')

    @compinit
    def __init__(self, out_path = '.', **kwargs):
       
        if (not os.path.isdir(self.out_path)):
            os.makedirs(self.out_path, exist_ok=True)
        
        sydsys().sim.events['run_end'].append(self.coverage_done)
        GreenletProfiler.set_clock_type('cpu')
        GreenletProfiler.start()
        