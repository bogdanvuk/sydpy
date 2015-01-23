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

"""Module that implements the Module class."""

from sydpy import seq, sig
from sydpy._util._util import get_arch_args
from sydpy.intfs._intf import IntfDir
from sydpy._component import Component
from sydpy._simulator import simproc_reg, simarch_inst_start, simarch_inst_stop
from sydpy._util._injector import RequiredFeature

class Module(Component):
    """Module class that all user modules should subclass."""
    _configurator = RequiredFeature('Configurator')
    
    def __init__(self, name, parent, arch=None, hdl_gen=False, scrbrd=None, intfs={}, **config):
        
        Component.__init__(self, name, parent)
        
        self.hdl_gen = hdl_gen
        self.intfs = intfs
        self.architectures = {}

        # If the arch is supplied via parameter
        if arch is not None:
            # If only one arch is supplied
            if isinstance(arch, str):
                self.arch_inst(arch, **config)
            else:
                # If multiple archs are supplied, the first one is active, others are passive. 
                # We have to redirect all outputs of the passive archs to new ad-hoc channels.
                
                dut_outputs = []
                ref_outputs = []
                active = True
                for a in arch:
                    self.arch_inst(a, active, **config)
                    
                    port_list = self.architectures[a]['port_list']
                    arch_config = self.architectures[a]['arch_config']
                    
                    if active:
                        for p in port_list:
                            if port_list[p].side == IntfDir.master:
                                dut_outputs.append(arch_config[p])
                                
                        active = False
                    else:
                        for p in port_list:
                            if port_list[p].side == IntfDir.master:
                                ref_outputs.append(arch_config[p])
                
                # If scoreboard is supplied, we instantiate it
                if scrbrd:
                    try:
                        scrbrd_conf = scrbrd[1]
                        scrbrd = scrbrd[0]
                    except TypeError:
                        scrbrd_conf = {}
                
                    self.inst(scrbrd, dut_i=dut_outputs[0], ref_i=ref_outputs[0], dut_name=arch[0], ref_name=arch[1], **scrbrd_conf)
        else:
            # If no arch is supllied, we search for the default arch
            
            for func in dir(self):
                if not func.startswith('_'):
                    if callable(getattr(self, func)):
                        if hasattr(getattr(self,func), "arch_def"):
                            self.arch_inst(func, **config)
                            return
    
    def get_channel(self, ch, side=IntfDir.slave):
        
        arch_active =self.architectures[self.current_arch]['active']
        
        if (not arch_active) and (side == IntfDir.master):
            if isinstance(ch, str):
                ch = ch + "_" + self.current_arch
            else:
                ch = ch.name + "_" + self.current_arch
        
        if isinstance(ch, str):
            elem, path = self.find(ch)
            if path:
                from sydpy._channel import Channel
                elem = elem.inst(Channel, path)
            
            return elem
        else:
            try:
                return ch._channel
            except AttributeError:
                return ch
    
    def intf(self, chnl, intf=None, init=None):
        proxy = self.proxy_from_conf(chnl, init=init, intf=intf)
        
        if proxy._intf is None:
            proxy.get_intf()
            
        return proxy
    
    def seq(self, dtype=None, master=None, slave=None, init=None, clk=None):
        if dtype is not None:
            intf = seq(dtype=dtype, module=self)
        else:
            intf = None
        
        if slave is not None:
            intf <<= slave
            
        if master is not None:
            intf >>= master
            
        if clk is not None:
            intf.clk <<= clk
            
        intf.init(init)

        return intf
            
    def sig(self, dtype=None, master=None, slave=None, init=None):
        if dtype is not None:
            intf = sig(dtype=dtype, module=self)
        else:
            intf = None
        
        if slave is not None:
            intf <<= slave
            
        if master is not None:
            intf >>= master
            
        intf.init(init)
        
        return intf
                
    def arch_inst(self, arch_func, arch_active=True, proxy_copy=False, **config):
        
        if isinstance(arch_func, str):
            arch_func = getattr(self, arch_func, None)
            
        if arch_func:
            arch_name = arch_func.__name__
            
            self.architectures[arch_name] = dict(func=arch_func, active=arch_active)
            self.current_arch = arch_name
            
            arch_config, port_list = self.create_arch_config(arch_func, arch_active, proxy_copy, **config)
            self.cur_arch_proc = []
            
            self.architectures[arch_name]['port_list'] = port_list
            self.architectures[arch_name]['arch_config'] = arch_config
            
#             print("Start: " + arch_name)
            simarch_inst_start()
            arch_func(**arch_config)
            simarch_inst_stop()
#             print("End: " + arch_name)
            
            self.architectures[arch_name]['proc'] = self.cur_arch_proc
               
#             if self.hdl_gen:
#                 module_toVerilog(self, arch_name)
    
    def proc_reg(self, proc):
        self.cur_arch_proc.append(proc)
        simproc_reg(proc)
    
    def get_channel_struct(self, chnl, arch_name=None, arch_active=True, intf=intf):
        if isinstance(chnl, str):
            if (not arch_active) and (intf.direction == IntfDir.master):
                chnl += "_" + arch_name
                    
            return self.get_channel(chnl)
        elif isinstance(chnl, tuple):
            channel = []
            for c in chnl:
                channel.append(self.get_channel_struct(c, arch_name=arch_name, arch_active=arch_active, intf=intf))
                
            return tuple(channel)
        elif isinstance(chnl, dict):
            channel = {}
            for c in chnl:
                try:
                    channel[c] = self.get_channel_struct(chnl[c], arch_name=arch_name, arch_active=arch_active, intf=getattr(intf, c))
                except AttributeError:
                    pass
                
            return channel
        else:
            try:
                #We have an Interface or Proxy for conf
                channel = chnl._channel
                
                try:
                    #Is it a proxy?
                    intf = chnl._intf
                except AttributeError:
                    #No it's an Interface
                    intf = chnl
                
                if (not arch_active) and (intf.direction == IntfDir.master):
                    conf = channel.name + "_" + arch_name
                    channel = self.parent.get_channel_struct(conf)
                    
            except AttributeError:
                if (not arch_active) and (intf.direction == IntfDir.master):
                    conf += "_" + arch_name
                
                channel = self.parent.get_channel_struct(conf)
                
            return channel
    
#     def proxy_from_conf(self, conf, intf=None, init=None, arch_name=None, arch_active=True):
#         if not isinstance(conf, SymNode):
#             if intf is None:
#                 try:
#                     try:
#                         #Is it a proxy?
#                         intf = conf._intf
#                     except AttributeError:
#                         #No it's an Interface
#                         intf = conf
#                 except AttributeError:
#                     pass
#                 
#             channel = self.parent.get_channel_struct(conf, arch_name=arch_name, arch_active=arch_active, intf=intf)
# 
#             return ChProxy(channel=channel, parent_module=self, intf=intf, init=init)
#         else:
#             intf = csig()
#             return ChProxy(channel=None, parent_module=self, intf=intf, init=conf)
    
    def assign_conf_to_intf(self, intf, chnl, arch_name=None, arch_active=True):
        if isinstance(chnl, str):
            if (not arch_active) and (intf._side == IntfDir.master):
                chnl += "_" + arch_name
                    
            return self.get_channel(chnl)
        elif isinstance(chnl, tuple):
            channel = []
            for c in chnl:
                channel.append(self.get_channel_struct(c, arch_name=arch_name, arch_active=arch_active, intf=intf))
                
            return tuple(channel)
        elif isinstance(chnl, dict):
            channel = {}
            for c in chnl:
                try:
                    channel[c] = self.get_channel_struct(chnl[c], arch_name=arch_name, arch_active=arch_active, intf=getattr(intf, c))
                except AttributeError:
                    pass
                
            return channel
        else:
            try:
                #We have an Interface or Proxy for conf
                channel = chnl._channel
                
                try:
                    #Is it a proxy?
                    intf = chnl._intf
                except AttributeError:
                    #No it's an Interface
                    intf = chnl
                
                if (not arch_active) and (intf.direction == IntfDir.master):
                    conf = channel.name + "_" + arch_name
                    channel = self.parent.get_channel_struct(conf)
                    
            except AttributeError:
                if (not arch_active) and (intf.direction == IntfDir.master):
                    conf += "_" + arch_name
                
                channel = self.parent.get_channel_struct(conf)
                
            return channel
        
#         if not proxy._has_intf:
#             if isinstance(conf, SymNode):
#                 intf = csig()
#             else:
#                 try:
#                     try:
#                         #Is it a channel proxy or an interface side proxy?
#                         proxy.set_intf(conf._intf)
#                     except AttributeError:
#                         #No it's an Interface
#                         proxy.set_intf(conf)
#                 except AttributeError:
#                     pass
    
    def uplevel_channels(self, conf):
        if isinstance(conf, str):
            if not conf.startswith('/'):
                return '../' + conf
        elif isinstance(conf, tuple):
            conf_up = []
            for c in conf:
                conf_up.append(self.uplevel_channels(c))
                
            return tuple(conf_up)
        elif isinstance(conf, dict):
            conf_up = {}
            for c, val in conf.items():
                try:
                    conf_up[c] = self.uplevel_channels(val)
                except AttributeError:
                    pass
                
            return conf_up
        else:
            return conf
    
    def create_arch_proxies(self, arch_func, proxy_copy, arch_config, arch_ports, arch_annot, arch_active):
        arch_proxies = {}
        for arg in arch_ports:
            intf = None
            conf = arch_config[arg]
            
            if isinstance(conf, str):
                if not conf.startswith('/'):
                    conf = '../' + conf
            
            if arg in arch_annot:
                if isinstance(arch_annot[arg], str):
                    intf = eval(arch_annot[arg], globals(), arch_config)
                else:
                    intf = arch_annot[arg]
                    
            if arg in self.intfs:
                intf = self.intfs[arg]

            if intf is not None:
                try:
                    intf_proxy = intf
                    intf = intf.intf
                except AttributeError:
                    intf_proxy = intf.slave
            
                intf_proxy.set_module(self)
                intf_proxy.connect(conf)
            
            else:
                intf = conf
                
                try:
                    intf_proxy = intf
                    intf = intf.intf
                except AttributeError:
                    intf_proxy = intf.slave
            
            arch_proxies[arg] = intf_proxy
            arch_config[arg] = intf_proxy.intf
                            
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
        
        return arch_config, arch_proxies
    
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
 
#         for arg in arch_ports:
#             conf = arch_config[arg]
# #             
# #             try:
# #                 #If we have an Interface or Proxy for conf
# #                 ch_passive = conf._channel.name + "_" + arch_func.__name__
# #                 
# #                 if (arg in arch_func.outputs) and (arch_active == False):
# #                     arch_config[arg] = self.parent.get_channel(ch_passive)
# #                     
# #             except AttributeError:
# #                 # We have a Channel
# #                 if (arg in arch_func.outputs) and (arch_active == False):
# #                     conf = conf  + "_" + arch_func.__name__
#                 
#             arch_config[arg] = self.parent.get_channel(conf)
                            
        return arch_config
    
    def create_arch_config(self, arch_func, arch_active, proxy_copy, **config):
        (arch_args, arch_ports, arch_confs, arch_arg_defs, arch_annot) = get_arch_args(arch_func)
        
        arch_config = self.update_arch_config(arch_args, arch_arg_defs, config, arch_ports, arch_func, arch_active)
        
        arch_config, arch_proxies = self.create_arch_proxies(arch_func, proxy_copy, arch_config, arch_ports, arch_annot, arch_active)
       
        return arch_config, arch_proxies
        