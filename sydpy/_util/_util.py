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

""" Module with utilility objects.

"""

import time
import inspect
import ast                                               

def timeit(method):
    """ Decorator for function execution timing """
    
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print('%r (%r, %r) %2.2f sec' % (method.__name__, args, kw, te-ts))
        return result

    return timed

def class_load(cls):
    """Instatiate class given by path string
    
    The format expected of the class path is:
    path.to.the.module.ClassName
    """
    if isinstance(cls, str):
        class_path_partition = cls.rpartition('.')
        
        class_name = class_path_partition[-1]
        module_name = class_path_partition[0]
        
        if not module_name:
            module_name = "sydpy"
        
        module = __import__(module_name, fromlist=[class_name])
        class_ = getattr(module, class_name)
        
        return class_
    else:
        return cls

def factory(cls, *args, **kwargs):
    class_load(cls)(*args, **kwargs)
    
def key_repr(key):
    if key is not None:
        if isinstance(key, slice):
            return '[{0}:{1}]'.format(key.start, key.stop)
        else:
            return '[{0}]'.format(key)
    else:
        return ''
    
def unif_enum(obj):
    if hasattr(obj, '__iter__'):
        for e in obj:
            yield e
    else:
        yield obj

from tokenize import generate_tokens, untokenize, INDENT
from io import StringIO

def _dedent(s):
    """Dedent python code string."""

    result = [t[:2] for t in generate_tokens(StringIO(s).readline)]
    # set initial indent to 0 if any
    if result[0][0] == INDENT:
        result[0] = (INDENT, '')
    return untokenize(result)

class _SigNameVisitor(ast.NodeVisitor):
    def __init__(self, symdict):
        self.inputs = {}
        self.outputs = {}
        self.toplevel = 1
        self.symdict = symdict
        self.keys = None
        self.proxy = None
        self.context = False
        self.subproxy = []

    def visit_Name(self, node):
        id = node.id
        if id not in self.symdict:
            self.subproxy = []
            return
        
        self.proxy = self.symdict[id]
        
        inp = True
        if self.subproxy:
#             if self.subproxy[0] == 'next':
#                 inp = True
#                 self.subproxy.pop(0)
            if self.subproxy[0] in ('next', 'next_after', 'write', 'blk_next'):
                inp = False
                self.subproxy.pop(0)
                 
            for s in reversed(self.subproxy):
                try:
                    self.proxy = getattr(self.proxy, s)
                except AttributeError:
                    self.subproxy = []
                    break
                
            self.subproxy = []
            
        if inp:
            self.inputs[repr(self.proxy)] = self.proxy
        else:
            self.outputs[repr(self.proxy)] = self.proxy

    def visit_Attribute(self, node):
        self.subproxy.append(node.attr)
        self.visit(node.value)
        
def get_arch_args(arch_func):
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

def getio_vars(func):
        
#     varnames = func.__code__.co_varnames
    symdict = {}

    try:    
        if func.arch == True:
            (arch_args, arch_ports, arch_confs, arch_arg_defs, arch_annot) = get_arch_args(func)
        
            for p in arch_ports:
                symdict[p] = p
                
    except AttributeError:
        pass

    if func.__code__.co_freevars:
        for n, c in zip(func.__code__.co_freevars, func.__closure__):
            try:
                symdict[n] = c.cell_contents
            except NameError:
                raise NameError(n)
    
    
    s = inspect.getsource(func)
    tree = ast.parse(_dedent(s))
    v = _SigNameVisitor(symdict)
    v.visit(tree)
    
    return list(v.inputs.values()), list(v.outputs.values())

# @decorator
def arch(f):
    f.inputs, f.outputs = getio_vars(f)
    return f

def arch_def(f):
    f.arch_def = True
    return arch(f)    
    
def fannotate(f, **kwargs):
    if not hasattr(f, '__annotations__'):
        f.__annotations__ = {}
    f.__annotations__.update(kwargs)

    return f
