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
from sydpy._channel import Channel
from sydpy._ch_proxy import ChProxy
from sydpy.aspects.sig import sig
from sydpy.aspects.bit import bit
from sydpy.aspects.seq import seq
from sydpy._simulator import simproc_reg
from sydpy._util._injector import RequiredFeature
import inspect

# @decorator
def architecture(f):
    f.arch = True   
    return f

class Module(Component):
    """Module class that all user modules should subclass."""
    _configurator = RequiredFeature('Configurator')
    
    def __init__(self, name, parent, arch=None, hdl_gen=False, **config):
        
        Component.__init__(self, name, parent)
        
        self.hdl_gen = hdl_gen
        self.architectures = {}

        if arch is not None:
            if isinstance(arch, str):
                self.arch_inst(arch, **config)
            else:
                for a in arch:
                    self.arch_inst(a, **config)
        else:
            archs = []
            for func in dir(self):
                if not func.startswith('_'): #and hasattr(getattr(self,func), "arch"):
                    if callable(getattr(self, func)):
                        try:
                            if hasattr(getattr(self,func), "arch"):
                                archs.append(func)
                        except:
                            pass
                
            if archs:
                self.arch_inst(archs[0], **config)
                
    def seq(self, name, aspect=None, clk=None):
        chnl = self.req_channel(name)
        clkch = ChProxy(self, self.req_channel(clk), sig(bit))
        
        return ChProxy(self, chnl, seq(aspect, clkch))
    
    def sig(self, name, aspect=None, val=None):
        
        chnl = self.req_channel(name)
        
        proxy = ChProxy(self, chnl, sig(aspect))
        
        if val is not None:
            proxy.next = val
    
        return proxy
    
    def arch_inst(self, arch_name, **config):
        arch_func = getattr(self, arch_name, None)
        if arch_func:
            self.architectures[arch_name] = None
            
            arch_config = self.create_arch_config(arch_func, **config)
            self.cur_arch_proc = []
            
            arch_func(**arch_config)
            
            self.architectures[arch_name] = (arch_func, arch_config, self.cur_arch_proc)
                
#             if self.hdl_gen:
#                 module_toVerilog(self, arch_name)
    
    def proc_reg(self, proc):
        self.cur_arch_proc.append(proc)
        simproc_reg(proc)
    
    def get_arch_args(self, arch_func):
        p = inspect.getfullargspec(arch_func)
        
        arch_args = [a for a in p.args]
        arch_args.pop(0)  #Exclude self
        
        if p.defaults:
            arch_arg_defs = [d for d in p.defaults]
        else:
            arch_arg_defs = []
        
        arch_port_map_len = len(arch_args) - len(arch_arg_defs)
        
        arch_ports = arch_args[:arch_port_map_len]
        arch_confs = arch_args[arch_port_map_len+1:]
        arch_arg_defs[:0] = [None]*(arch_port_map_len)
        
        return arch_args, arch_ports, arch_confs, arch_arg_defs, p.annotations
    
    def create_arch_proxies(self, arch_func, arch_config, arch_ports, arch_annot):
        
        for arg in arch_ports:
            conf = arch_config[arg]
            
            try:
                aspect = conf.aspect
            except AttributeError:
                aspect = None

            if arg in arch_annot:
                if isinstance(arch_annot[arg], str):
                    aspect = eval(arch_annot[arg], globals(), arch_config)
                else:
                    aspect = arch_annot[arg]
            
            try:
                arch_config[arg] = ChProxy(self, conf.channel, aspect)
            except AttributeError:
                arch_config[arg] = ChProxy(self, conf, aspect)
        
        return arch_config
    
    def create_arch_config(self, arch_func, **config):
        (arch_args, arch_ports, arch_confs, arch_arg_defs, arch_annot) = self.get_arch_args(arch_func)
        arch_config = {}
        for arg in zip(arch_args, arch_arg_defs):
            if arg[0] in config:
                arch_config[arg[0]] = config[arg[0]]
            else:
                arch_config[arg[0]] = arg[1]
        
        try:
            self._configurator.update_config(self.qualified_name, arch_config)
        except KeyError:
            pass
 
        for arg in arch_ports:
            conf = arch_config[arg]
            if isinstance(conf, str):
                elem, path = self.parent.find(conf)
                
                if path:
                    elem = self.parent.inst(Channel, path)
                    
                arch_config[arg] = elem
        
        return self.create_arch_proxies(arch_func, arch_config, arch_ports, arch_annot)    
       
        