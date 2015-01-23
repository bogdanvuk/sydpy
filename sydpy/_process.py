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

"""Module that implements various process decorators."""

from greenlet import greenlet
from sydpy._util._util import getio_vars
from sydpy._simulator import simwait

class Process(greenlet):
    """Wrapper class for functions that implement processes in user modules.
    
    Class turns function in the greenlet task.""" 
   
    def __init__(self, module, func, *args, exit_func=None, **kwargs):
        self.func = func
        self.func_params = kwargs
        self.module = module
        self.arch = self.module.current_arch
        self.module.proc_reg(self)
        self.name = module.qualified_name + "." + func.__name__
        senslist = []
        
        for a in args:
            if hasattr(a, 'subscribe'):
                senslist.append(a)
        
        self.senslist = senslist
        self._exit_func = exit_func
        
        # If the module is to be traslated to HDL, translate the process
        if module.hdl_gen:
            self.hdl_gen()
        
        greenlet.__init__(self)
    
    def run(self):
        if self.senslist:
            while(1):
                simwait(self.senslist)
                self.func(**self.func_params)
        else:
            self.func(**self.func_params)
            simwait()
            
    def exit_func(self):
        if self._exit_func:
            self._exit_func()
   
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.__str__()
    
class AlwaysAcquire(Process):
    """Wrapper class for functions that implement processes in user modules.
    
    This wrapper is used for processes with single interface in sensitivity
    list. The process is triggered when a new value can be popped via 
    interface."""
     
    def run(self):
        arch_active = self.module.architectures[self.arch]['active']
        while(1):
            if arch_active:
                val = self.senslist[0].blk_pop()
            else:
                simwait(self.senslist[0].e.updated)
                val = self.senslist[0].read()
                
            self.func(val, **self.func_params)
         
def always_comb(self):
    """This process decorator automatically derives the sensitivity list for 
    the process from the code."""

    def _always_decorator(func):
        (inputs, outputs) = getio_vars(func)

        Process(self, func, *inputs)

    return _always_decorator

def always_acquire(self, *args, **kwargs):
    """This process decorator instantiates the AlwaysAcquire object for the process."""
    
    def _always_decorator(func):
        AlwaysAcquire(self, func, args[0], **kwargs)
    
    return _always_decorator   

def always(self, *args, **kwargs):
    """This process decorator instantiates the Process wrapper object for the process."""
    
    def _always_decorator(func):
        Process(self, func, *args, **kwargs)
    
    return _always_decorator
