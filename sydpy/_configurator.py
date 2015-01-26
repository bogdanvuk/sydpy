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

"""Module that handles the configuration dictionaries."""

import fnmatch

class Configurator(object):
    """Class for handling configuration dictionaries."""

    def update_config(self, qualified_name, config):
        """Update the values of the passed config dictionary.
        
        The values of the config are updated according to the
        entries of the configuration contained with in the 
        Configuration object.
        """
        for p_pat in self.config:
            # For every key in Configuration dict, try to match it
            # with keys of the passed config dict.
            if fnmatch.fnmatch(qualified_name, p_pat):
                for c_pat in self.config[p_pat]:
                    for c in config:
                        if fnmatch.fnmatch(c, c_pat):
                            config[c] = self.config[p_pat][c_pat]
    
    def __setitem__(self, args, val):
        comp = args[0]
        cfg = args[1]
        
        if comp not in self.config:
            self.config[comp] = {}
            
        self.config[comp][cfg] = val
    
    def __getitem__(self, args):
        
        comp = args[0]
        cfg = args[1]
        
        if len(args) == 2:
            return self.config[comp][cfg]
        else:
            dflt = args[2]
            
            if comp in self.config:
                if cfg in self.config[comp]:
                    return self.config[comp][cfg]
        
        return dflt
    
    def __init__(self, config):
        '''
        Constructor
        '''
        
        self.config = {}
        
        for c in config:
            path_pat, dummy , conf_pat = c.rpartition('.')
            
            path_pat = path_pat.replace('[', '(').replace(']', ')')
            
            path_pat = path_pat.replace('(', '[[]').replace(')', '[]]')
            
            if path_pat not in self.config:
                self.config[path_pat] = {}
                
            self.config[path_pat][conf_pat] = config[c]

