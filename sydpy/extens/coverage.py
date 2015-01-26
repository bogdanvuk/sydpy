'''
Created on Oct 17, 2014

@author: bvukobratovic
'''

from coverage import coverage
from sydpy._util._injector import RequiredVariable

class Coverage(object):

    def coverage_done(self, sim):
        self.cov.stop()
        self.cov.html_report(directory=self.out_path)    

    def __init__(self, sim_events):
        self.configurator = RequiredVariable('Configurator')
        self.include = self.configurator['Coverage', 'include', []]
        self.branching = self.configurator['Coverage', 'branching', False]
        self.out_path = self.configurator['Coverage', 'path', self.configurator['sys', 'output_path', self.configurator['sys', 'project_path'] + "/out/coverage"]]
        self.project_path = self.configurator['sys', 'project_path']
        
        for i in range(len(self.include)):
            self.include[i] = self.project_path + "/" + self.include[i]
        
        sim_events['run_end'].append(self.coverage_done)
        self.cov = coverage(include=self.include, branch=self.branching, concurrency='greenlet')
        self.cov.start()
        