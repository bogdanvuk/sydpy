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
from sydpy._util._symexp import SymNode
from sydpy._util._util import get_arch_args, getio_vars

"""Module that implements the Module class."""

from sydpy._component import Component
from sydpy._ch_proxy import ChProxy
from sydpy.intfs import sig, seq, tlm
from sydpy.types import bit
from sydpy._simulator import simproc_reg, simarch_inst_start, simarch_inst_stop, simarch_inst
from sydpy._util._injector import RequiredFeature
import inspect

class Module(Component):
    """Module class that all user modules should subclass."""
    _configurator = RequiredFeature('Configurator')
    
    def __init__(self, name, parent, arch=None, hdl_gen=False, scrbrd=None, intfs={}, **config):
        
        Component.__init__(self, name, parent)
        
        self.hdl_gen = hdl_gen
        self.intfs = intfs
        self.architectures = {}

        if arch is not None:
            if isinstance(arch, str):
                self.arch_inst(arch, **config)
            else:
                
                outputs = []
                active = True
                for a in arch:
                    self.arch_inst(a, active, **config)
                    
                    if active:
                        output_names = self.architectures[arch[0]]['func'].outputs
                        active = False
                        
                    outputs.append(self.architectures[a]['config'][output_names[0]])
                
                if scrbrd:
                    try:
                        scrbrd_conf = scrbrd[1]
                        scrbrd = scrbrd[0]
                    except TypeError:
                        scrbrd_conf = {}
                
#                 for o in outputs:
#                     if isinstance(o.intf, tlm):
#                         intf = o.intf
#                         break
# 
#                 scrbrd_conf.update({'dut_i': intf, 'ref_i': intf})
                    
#                 dut_p = ChProxy(self, outputs[0].channel, intf)
#                 ref_p = ChProxy(self, outputs[1].channel, intf)
                                                   
                self.inst(scrbrd, dut_i=outputs[0], ref_i=outputs[1], dut_name=arch[0], ref_name=arch[1], **scrbrd_conf)
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
    
    def get_channel(self, ch):
        if isinstance(ch, str):
            elem, path = self.parent.find(ch)
            if path:
                from sydpy._channel import Channel
                elem = self.parent.inst(Channel, path)
            
            return elem
        else:
            try:
                return ch._channel
            except AttributeError:
                return ch
                
    def seq(self, name, dtype=None, clk=None, init=None):
        chnl = self.get_channel(name)

        if not isinstance(clk, ChProxy):
#             clk = ChProxy(self, self.get_channel(clk), sig(bit))
            clk = NoneIntf(channel=self.get_channel(clk))
        
#         if (dtype is not None) and (init is not None):
#             init = dtype(init)
        
#         proxy = ChProxy(self, chnl, seq(dtype), init=init)

        proxy = seq(dtype=dtype, channel=chnl, parent_module=self, init=init)

        proxy.clk = clk
        
        return proxy
    
    def sig(self, name, dtype=None, init=None):
        
        chnl = self.get_channel(name)
        
        proxy = sig(dtype, channel=chnl, parent_module=self, init=init)
        
#         proxy = ChProxy(self, chnl, sig(dtype), init=init)

        return proxy
    
    def arch_inst(self, arch_func, arch_active=True, proxy_copy=False, **config):
        
        if isinstance(arch_func, str):
            arch_func = getattr(self, arch_func, None)
            
        if arch_func:
            self.architectures[arch_func.__name__] = None
            
            arch_config = self.create_arch_config(arch_func, arch_active, proxy_copy, **config)
            self.cur_arch_proc = []
            self.architectures[arch_func.__name__] = dict(func=arch_func,
                                                          active=arch_active,
                                                          config=arch_config)
            self.current_arch = arch_func.__name__
            
            simarch_inst_start()
            arch_func(**arch_config)
            simarch_inst_stop()
            
            self.architectures[arch_func.__name__]['proc'] = self.cur_arch_proc
               
#             if self.hdl_gen:
#                 module_toVerilog(self, arch_name)
    
    def proc_reg(self, proc):
        self.cur_arch_proc.append(proc)
        simproc_reg(proc)
    
    def create_arch_proxies(self, arch_func, proxy_copy, arch_config, arch_ports, arch_annot):
        
        for arg in arch_ports:
            conf = arch_config[arg]
            
            if not isinstance(conf, SymNode):
                intf = None
                
                try:
                    channel = conf._channel
                    
#                     #Proxy was passed as configuration
#                     if proxy_copy:
#                         arch_config[arg] = ChProxy(self, conf.channel, intf, proxy_copy=True)
#                     
#                     continue
                except AttributeError:
                    channel = conf
    
                if arg in arch_annot:
                    if isinstance(arch_annot[arg], str):
                        intf = eval(arch_annot[arg], globals(), arch_config)
                    else:
                        intf = arch_annot[arg]
                        
                if arg in self.intfs:
                    intf = self.intfs[arg]

                if (intf is None) and isinstance(conf, ChProxy):
                    continue
                else:
                    arch_config[arg] = ChProxy(channel=channel, parent_module=self, intf=intf)
                
#                 try:
#                     if proxy_intf is not None:
#                         if proxy_copy or ((proxy_intf != intf) and (intf is not None)):
#                             
#                             if intf is None:
#                                 intf = proxy_intf
#                             
#                             arch_config[arg] = ChProxy(self, conf.channel, intf, proxy_copy=proxy_copy)
#                     else:
#                         arch_config[arg] = ChProxy(self, conf, intf)
#                 except AttributeError:
#                     arch_config[arg] = ChProxy(self, conf, intf)
        
        return arch_config
    
    def update_arch_config(self, arch_args, arch_arg_defs, config, arch_ports, arch_func, arch_active):
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
            
            if (arg in arch_func.outputs) and (arch_active == False):
                if isinstance(conf, ChProxy):
                    conf = conf._channel.name + "_" + arch_func.__name__
                else:
                    conf = conf  + "_" + arch_func.__name__

            if not isinstance(conf, ChProxy):
                arch_config[arg] = self.get_channel(conf)
                
        return arch_config
    
    def create_arch_config(self, arch_func, arch_active, proxy_copy, **config):
        (arch_args, arch_ports, arch_confs, arch_arg_defs, arch_annot) = get_arch_args(arch_func)
        
        arch_config = self.update_arch_config(arch_args, arch_arg_defs, config, arch_ports, arch_func, arch_active)
        
        return self.create_arch_proxies(arch_func, proxy_copy, arch_config, arch_ports, arch_annot)    
       
        