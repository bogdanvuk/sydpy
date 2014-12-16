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

"""Module that implements the Module class."""

from sydpy._component import Component

class Module(Component):
    """Module class that all user modules should subclass."""
    
    def seq(self, name, aspect=None, clk=None):
        chnl = self.req_channel(name)
        clkch = ChProxy(self, self.req_channel(clk), sig(bit))
        
        return ChProxy(self, chnl, seq(aspect, clkch))
    
    def sig(self, name, aspect=None, val=None):
        
        chnl = self.req_channel(name)
        
        proxy = ChProxy(self, chnl, sig(aspect))
        
        if val is not None:
            proxy.next = val
        
#         sig = chnl._req_proxy_sig(proxy)
#         chnl.proxy_set_drive(proxy, sig)
    
        return proxy
    
    def get_arch_args(self, arch_func):
        p = inspect.getfullargspec(arch_func)
        
        arch_args = [a for a in p.args]
        arch_args.pop(0)  #Exclude self
        
        if p.defaults:
            arch_arg_defs = [d for d in p.defaults]
        else:
            arch_arg_defs = []
        
        arch_port_map_len = len(arch_args) - len(arch_arg_defs)
        
        arch_args = arch_args[:arch_port_map_len]
        
        return arch_args
    
    def get_arch_annotations(self, arch_func):
        p = inspect.getfullargspec(arch_func)
        
        return p.annotations
        
    
    def create_arch_proxies(self, arch_func, arch_config, proxy_srcs={}):
        
        arch_args = self.get_arch_args(arch_func)
        annotations = self.get_arch_annotations(arch_func)
        
        for arg in arch_args:
            conf = arch_config[arg]
            
            try:
                aspect = conf.aspect
            except AttributeError:
                aspect = None

            if arg in annotations:
                if isinstance(annotations[arg], str):
                    aspect = eval(annotations[arg], globals(), arch_config)
                else:
                    aspect = deepcopy(annotations[arg])
            
            try:
                arch_config[arg] = ChProxy(self, conf.channel, aspect)
            except AttributeError:
                arch_config[arg] = ChProxy(self, self.req_channel(conf), aspect)
        
        return arch_config
    
    def create_arch_config(self, arch_func, **config):
        
        if 'proxy_srcs' in config:
            proxy_srcs = config['proxy_srcs']
        else:
            proxy_srcs = {}
        
        arch_config = ModuleBase.create_arch_config(self, arch_func, **config)
        
        return self.create_arch_proxies(arch_func, arch_config, proxy_srcs)    
    
    def req_channel(self, name, aspect=""):
        if name in self.components:
            return self.components[name]
        else:
            return self.inst(Channel, name)