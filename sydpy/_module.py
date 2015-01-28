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

from sydpy._util._util import get_arch_args
from sydpy.intfs._intf import IntfDir
from sydpy._component import Component
from sydpy._simulator import simproc_reg, simarch_inst_start, simarch_inst_stop
from sydpy._util._injector import RequiredFeature
from sydpy import *

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
        """Retreive the channel from the parameter ch.
        
        Parameter ch can be either:
        1. a string: Channel is searched by qualified name within the 
            hierarchy of components. If channel is not found, it is 
            created and returned.
        2. a Channel object
         
        """
        
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
    
    def _intf_con(self, intf, master=None, slave=None, init=None):
        """Connect the interface."""
    
        if slave is not None:
            intf <<= slave
            
        if master is not None:
            intf >>= master
            
        intf.init(init)
    
    def seq(self, dtype, master=None, slave=None, init=None, clk=None):
        """Create a new seq interface and connect it to other interfaces or channels.
        
        dtype      - Data type of the data signal
        master     - Interface of channel to which to connect as the master
        slave      - Interface of channel to which to connect as the slave
        init       - Initial value to write to channel
        clk        - Clk interface or channel to supply to clk signal
        """ 
        
        intf = seq(dtype=dtype, module=self)

        self._intf_con(intf, master, slave, init)
        
        if clk is not None:
            intf.clk <<= clk

        return intf
            
    def sig(self, dtype, master=None, slave=None, init=None):
        """Create a new sig interface and connect it to other interfaces or channels.
        
        dtype      - Data type of the signal
        master     - Interface of channel to which to connect as the master
        slave      - Interface of channel to which to connect as the slave
        init       - Initial value to write to channel
        """
        
        intf = sig(dtype=dtype, module=self)
        
        self._intf_con(intf, master, slave, init)
        
        return intf
    
    def tlm(self, dtype, master=None, slave=None, init=None):
        """Create a new tlm interface and connect it to other interfaces or channels.
        
        dtype      - Data type of the signal
        master     - Interface of channel to which to connect as the master
        slave      - Interface of channel to which to connect as the slave
        init       - Initial value to write to channel
        """
        
        intf = tlm(dtype=dtype, module=self)
        
        self._intf_con(intf, master, slave, init)
        
        return intf
                
    def arch_inst(self, arch_func, arch_active=True, **config):
        """Instantiate a new module architecture, update the configuration and connect the proxies.
        
        arch_func      - The function that implements the architecture
        arch_active    - Is the architecture active
        config         - Configuration that was passed within module instantiation.
        """
        
        # If the function is supplied as a string, get the member function
        if isinstance(arch_func, str):
            arch_func = getattr(self, arch_func, None)
            
        if arch_func:
            arch_name = arch_func.__name__
            
            self.architectures[arch_name] = dict(func=arch_func, active=arch_active)
            self.current_arch = arch_name
            
            arch_config, port_list = self.create_arch_config(arch_func, arch_active, **config)
            self.cur_arch_proc = []
            
            self.architectures[arch_name]['port_list'] = port_list
            self.architectures[arch_name]['arch_config'] = arch_config
            
            simarch_inst_start()
            arch_func(**arch_config)
            simarch_inst_stop()
            
            self.architectures[arch_name]['proc'] = self.cur_arch_proc
               
#             if self.hdl_gen:
#                 module_toVerilog(self, arch_name)
    
    def proc_reg(self, proc):
        """ Interface for a process to register itself within its module."""
        self.cur_arch_proc.append(proc)
        simproc_reg(proc)
    
    def connect_arch_intfs(self, arch_func, arch_config, arch_ports, arch_annot, arch_active):
        """Connects the arch interfaces to the external channels and interfaces. """
        
        arch_intfs = {}
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
            
            arch_intfs[arg] = intf_proxy
            arch_config[arg] = intf_proxy.intf
        
        return arch_config, arch_intfs
    
    def update_arch_config(self, arch_args, arch_arg_defs, config, arch_ports, arch_func, arch_active):
        """Updates the architecture configuration from the global configuration. """
        
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
                            
        return arch_config
    
    def create_arch_config(self, arch_func, arch_active, **config):
        (arch_args, arch_ports, arch_confs, arch_arg_defs, arch_annot) = get_arch_args(arch_func)
        
        arch_config = self.update_arch_config(arch_args, arch_arg_defs, config, arch_ports, arch_func, arch_active)
        
        arch_config, arch_intfs = self.connect_arch_intfs(arch_func, arch_config, arch_ports, arch_annot, arch_active)
       
        return arch_config, arch_intfs
        