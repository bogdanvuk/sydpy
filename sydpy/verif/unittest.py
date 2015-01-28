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

"""Module implements classes for performing multiple tests on the design."""

from sydpy._simulator import Simulator
from sydpy._component import component_visitor

class UnitTestResult(object):
    
    def check_scoreboard_failed(self, sim):
    
        self.scoreboard_results = []
        component_visitor(sim.top_module, before_comp=lambda c: self.scoreboard_results.append(c.scoreboard_results) if hasattr(c, 'scoreboard_results') else False)
        
        if self.verbose:
            print('-'*80)
            print('-{:^78}-'.format('Scoreobard results'))
            print('-'*80)
        
        passed = True
        
        for s in self.scoreboard_results:
            if self.verbose:
                print(self.test_name + ":")
                
            for r in s['results']:
                if not r['score']:
                    if self.verbose:
                        print('Test failed!')
                        print(r['data'])
                    
                    passed = False
                    break
            else:
                if self.verbose:
                    print('Test passed!')
                
        return passed
    
    def __str__(self):
        return "Test for '" + self.test_name + "' " + ("passed." if self.result else "failed!")  
    
    def __bool__(self):
        return self.result
    
    def __init__(self, sim, test_name, verbose=False):
        self.test_name = test_name
        self.verbose = verbose
        self.result = self.check_scoreboard_failed(sim)

class UnitTest(object):
    
    def __iter__(self):
        for conf in self.configs:
            test_name = conf[1]
            conf = conf[0]
            
            if isinstance(conf, str):
                conf_path = conf
                
                conf_path_partition = conf_path.rpartition('.')
                
                class_name = conf_path_partition[-1]
                module_name = conf_path_partition[0]
                
                module = __import__(module_name, fromlist=[class_name])
                conf = getattr(module, class_name)
                
            if self.deal_outs:
                
                if hasattr(conf, 'sys.output_path'):
                    conf['sys.output_path'] = conf['sys.output_path'] + "/" + test_name
                else:
                    conf['sys.output_path'] = "./out/" + test_name
                
            sim = Simulator(conf)
            sim.run()
                         
            yield UnitTestResult(sim, test_name, verbose=self.verbose) 
    
    def __init__(self, configs=[], deal_outs=True, verbose=False):
        self.configs = configs
        self.deal_outs = deal_outs
        self.verbose = verbose
        
    