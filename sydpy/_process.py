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

"""Module that implements various process decorators."""

from greenlet import greenlet
from sydpy._simulator import simwait
import ast

class Process(greenlet):
    """Wrapper class for functions that implement processes in user modules.
    
    Class turns function in the greenlet task.""" 
   
    def __init__(self, module, func, *args, exit_func=None, **kwargs):
        self.func = func
        self.func_params = kwargs
        self.module = module
        self.module.proc_reg(self)
        self.name = module.qualified_name + "." + func.__name__
        self.senslist = args
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
         
# class Always(Process):
# #     hdl_gen = always_toVerilog
#     
#     def run(self):
#         while(1):
#             if self.senslist:
# #                 self.simulator.sched.switch(self.senslist)
#                 simwait(self.senslist)
#             self.func(**self.func_params)
            
# class AlwaysComb(Always):
#     hdl_gen = always_comb_toVerilog

import textwrap

INPUT, OUTPUT, INOUT = range(3)

class _SigNameVisitor(ast.NodeVisitor):
    def __init__(self, symdict):
        self.inputs = set()
        self.outputs = set()
        self.toplevel = 1
        self.symdict = symdict
        self.dir = INPUT
        self.keys = None
        self.proxy = None
        self.context = False

    def visit_Module(self, node):
#         inputs = self.inputs
#         outputs = self.outputs
        for n in node.body:
            self.visit(n)
#         for n in inputs:
#             if n in outputs:
#                 raise AlwaysCombError(_error.SignalAsInout % n)

    def visit_FunctionDef(self, node):
        if self.toplevel:
            self.toplevel = 0 # skip embedded functions
            for n in node.body:
                self.visit(n)
        else:
            raise AlwaysCombError(_error.EmbeddedFunction)

    def visit_If(self, node):
        if not node.orelse:
            if isinstance(node.test, ast.Name) and \
               node.test.id == '__debug__':
                return # skip
        self.generic_visit(node)

    def visit_Name(self, node):
        id = node.id
        if id not in self.symdict:
            return
        
        self.proxy = self.symdict[id]
        
        if not self.context:
            if isinstance(self.proxy, ChannelProxy):
                if self.dir == INPUT:
                    self.inputs.add(self.proxy)
                elif self.dir == OUTPUT:
                    self.outputs.add(self.proxy)
                else:
                    raise AssertionError("bug in always_comb")
            
    def visit_Assign(self, node):
        self.dir = OUTPUT
        for n in node.targets:
            self.visit(n)
        self.dir = INPUT
        self.visit(node.value)

    def visit_Attribute(self, node):
        self.visit(node.value)

    def visit_Call(self, node):
        fn = None
        if isinstance(node.func, ast.Name):
            fn = node.func.id
        if fn == "len":
            pass
        else:
            self.generic_visit(node)
            

    def visit_Subscript(self, node, access=INPUT):
        self.context = True
        self.visit(node.value)
        self.visit(node.slice)

        if isinstance(self.proxy, ChannelProxy):
            if self.keys is not None:
                self.proxy = self.proxy.__getitem__(self.keys)
 
            if self.dir == INPUT:
                self.inputs.add(self.proxy)
            elif self.dir == OUTPUT:
                self.outputs.add(self.proxy)
            else:
                raise AssertionError("bug in always_comb")
        
        self.context = False
        self.keys = None
        self.proxy = None

    def visit_AugAssign(self, node, access=INPUT):
        self.dir = INOUT
        self.visit(node.target)
        self.dir = INPUT
        self.visit(node.value)
    
    def visit_Index(self, node):
        self.keys = ast.literal_eval(node.value)
        pass
    
    def visit_Slice(self, node):
        low = ast.literal_eval(node.lower)
        high = ast.literal_eval(node.upper)
        self.keys = slice(high, low)
    
    def visit_Tuple(self, node):
        for n in node.elts:
            self.visit(n)
    
    def visit_ClassDef(self, node):
        pass # skip

    def visit_Exec(self, node):
        pass # skip

    def visit_Print(self, node):
        pass # skip

def always_comb(self):
    
    def _always_decorator(func):
        
        s = inspect.getsource(func)
        varnames = func.__code__.co_varnames
        symdict = {}
    #     for n, v in func.func_globals.items():
    #         if n not in varnames:
    #             symdict[n] = v
        # handle free variables
        if func.__code__.co_freevars:
            for n, c in zip(func.__code__.co_freevars, func.__closure__):
                try:
    #                 obj = _cell_deref(c)
                    symdict[n] = c.cell_contents
                except NameError:
                    raise NameError(n)
        
        tree = ast.parse(textwrap.dedent(s))
        v = _SigNameVisitor(symdict)
        v.visit(tree)

        AlwaysComb(self, func, *list(v.inputs))

    return _always_decorator
   

def always(self, *args, **kwargs):
    def _always_decorator(func):
        Process(self, func, *args, **kwargs)
    
    return _always_decorator
