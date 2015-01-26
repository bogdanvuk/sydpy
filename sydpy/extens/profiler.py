'''
Created on Oct 17, 2014

@author: bvukobratovic
'''

import GreenletProfiler
from sydpy._util._injector import RequiredVariable
import os

class Profiler(object):

    def coverage_done(self, sim):
        GreenletProfiler.stop()
        stats = GreenletProfiler.get_func_stats()
        stats.print_all(filter_in=['*sydpy*'])
        stats.save(self.out_path + '/profile.callgrind', type='callgrind')

    def __init__(self, sim_events):
        self.configurator = RequiredVariable('Configurator')
        self.out_path = self.configurator['Profiler', 'path', self.configurator['sys', 'output_path', self.configurator['sys', 'project_path'] + "/out/profile"]]
        
        if (not os.path.isdir(self.out_path)):
            os.makedirs(self.out_path, exist_ok=True)
        
        sim_events['run_end'].append(self.coverage_done)
        GreenletProfiler.set_clock_type('cpu')
        GreenletProfiler.start()
        