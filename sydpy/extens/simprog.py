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

from sydpy._util._injector import RequiredFeature

class SimtimeProgress(object):
    
    configurator = RequiredFeature('Configurator')

    def log_begin_timestep(self, time, sim):
        if time > (self.old_time + self.step):
            self.old_time = (time // self.step) * self.step
            print("--{0}--".format(self.old_time))
            
        return True

    def __init__(self, sim_events):
        self.step = self.configurator['SimtimeProgress', 'step', 100]
        
        sim_events['timestep_start'].append(self.log_begin_timestep)
        self.old_time = 0