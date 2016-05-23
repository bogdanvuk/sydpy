import fnmatch
import inspect
import re
from sydpy import ddic
from ddi.ddi import anonymous
import random
# from sydpy.sydpy import system

sep = '/'

class Component:
    """Component class is the base class for all objects that are part of the user 
    object hierarchy.    
    """
    
#    comp = {}
#    __cur_parent_class__ = None
    
    def __init__(self, name=None):
        """Instantiate a new compinit
         
        name    -- The name of the compinit
        """
        self.name = name
        self.c = {}
#         ddic.provide(self.qname, self)

#     def __init__(self, name=None, parent=None, **kwargs):
#         """Instantiate a new compinit
#         
#         name    -- The name of the compinit
#         """
#         self.name = name
#         self._parent = parent
#         if parent is not None:
#             self._parent.comp[name] = self
#         self.comp = {}

#         self._parent = parent
#         if parent is not None:
#             self._parent.c[name] = self
#         self.c = {}
#         ddic.provide(self.qname, self)

#     @property
#     def qname(self):
#         if self.name:
#             if self._parent:
#                 return sep.join([self._parent.qname, self.name])
# 
#         return self.name

    def __repr__(self):
        return self.name

#     def __setitem__(self, key, val):
#         try:
#             val = sydsys().get_config(self.name, key)
#         except KeyError: 
#             pass
#         
#         self.comp[key] = val
#         
#         return val
    
#     def __getitem__(self, key):
# #         return ddic[sep.join([self.name, key])]
#         return self._comp[key]
    
#     def __contains__(self, key):
#         return key in self._comp

    def inst(self, cls, name='', *args, **kwargs):
        c_name = name
        if anonymous(c_name):
            c_name += 'c' + str(random.randint(0, 1e8))

        name = sep.join([self.name, c_name])

        ddic.provide_on_demand(sep.join(['cls', name]), cls, name, inst_args = (name,) + args, inst_kwargs = kwargs)
        
        if name in ddic:
            c = ddic[name]
            self.c[c_name] = c
#             setattr(self, c_name, c)
            return c
        else:
            return None
        
    def __getattr__(self, name):
        try:
            return super().__getattr__(name)
        except AttributeError:
            if name in self.c:
                return self.c[name]
            else:
                raise
    
#         self.comp[key] = val
#     
#     def __getitem__(self, key):
# #         return ddic[sep.join([self.qname, key])]
#         return self.comp[key]

#     def inst(self, name, cls, *args, **kwargs):
#         try:
#             val = sydsys().get_config(self.name, name)
#             if not inspect.isclass(val):
#                 setattr(self, name, val)
#                 return val
#             else:
#                 cls = val
#         except KeyError: 
#             pass
#         
#         
#         if self.name:
#             qname = self.name + '.' + name
#         else:
#             qname = name
#         
#         obj = cls(qname, *args , **kwargs)
#         
#         self.comp[name] = obj
#         
#         return obj
#     
    def search(self, pattern='*', of_type=None, depth=0, pattern_relative=True):
         
        if pattern_relative:
            if self.name:
                pattern = sep.join([self.name, pattern])
 
        for _, c in self.c.items():
            if fnmatch.fnmatch(c.name, pattern):
                if (of_type is None) or isinstance(c, of_type):
                    yield c
                     
                if depth:
                    yield from c.search(pattern, pattern_relative=False, depth=depth-1)
    
#     def __getattr__(self, name):
#         try:
#             return self.comp[name]
#         except KeyError:
#             raise AttributeError(name)

def inst(cls, name, *args, **kwargs):
    if anonymous(name):
        name += str(random.randint(0, 1e8))

    ddic.provide_on_demand(sep.join(['cls', name]), cls, name, inst_args = (name,) + args, inst_kwargs = kwargs)
    
    if name in ddic:
        return ddic[name]
    else:
        return None

class System(Component):
    
    def __init__(self, name=''):
        Component.__init__(self, name)
        self._conf = {}
        self.providers = {}
        self.index = {}
        self.config = []
        
#     def __getitem__(self, path):
#         item = list(self.search(path, depth=1000))
#         if not item:
#             attr_name = path.split('.', 1)[0]
# #             val = self.get_config('', attr_name)
#             self.inst(attr_name, None)
#            
#         return self.index[path]
    
#     def __setitem__(self, path, val):
#         self.index[path] = val
    
#     def __getattr__(self, name):
#         if name not in sydsys().comp:
#             sydsys().inst(name, None)
#             
#         try:
#             return self.comp[name]
#         except KeyError:
#             raise AttributeError(name)
#     
        

    
#     
#         path = path.split('.')
#         comp = self
#         for p in path:
#             comp = getattr(comp, p)
#     
#         return comp

    def _create_index_rec(self, comp):
        index = {}
        for k,v in comp.__dict__.items():
            if isinstance(v, Component):
                if (comp == self) or (v.name == comp.name + '.' + k):
                    index[v.name] = v
                    index.update(self._create_index_rec(v))
        
        return index

    def update_index(self):
        self.index = self._create_index_rec(self)

        

#     def findall(self, pattern='*', of_type=None):
# #         self.update_index()
#         comps = {}
#         for k in fnmatch.filter(self.index.keys(), pattern):
#             comp = self.index[k]
#             if (of_type is None) or (isinstance(comp, of_type)):
#                 comps[k] = comp
#                  
#         return comps

    def set_config(self, config):
#         self.comp.clear()
        self.config = config
#         params = self.get_all_attrs('')
#         for p,v in params.items():
#             if p not in self.comp:
#                 self.inst(p, v)
    
    def get_config(self, comp_qualified_name, attr_name):
        if comp_qualified_name:
            qualified_name = comp_qualified_name + '.' + attr_name
        else:
            qualified_name = attr_name
            
        for conf in reversed(self.config):
            if fnmatch.fnmatch(qualified_name, conf[0]):
                return conf[1]
        
        raise KeyError
    
    def get_all_attrs(self, comp_qualified_name):
        attrs = {}
        
        for conf in self.config:
            if comp_qualified_name:
                names = conf[0].rsplit('.', 1)
                # if there exists clear compinit.attribute syntax for the conf
                if len(names) > 1:
                    # we are listing the attributes, so no wildcards allowed
                    if re.match(r'\w+$', names[1]) and fnmatch.fnmatch(comp_qualified_name, names[0]):
                        attrs[names[1]] = conf[1]
            else:
                # we are listing the attributes, so no wildcards allowed
                if conf[0].isalnum():
                    attrs[conf[0]] = conf[1]
        
        return attrs
    
    def update_params(self, comp_qualified_name, params):
        """Update the values of the passed params dictionary.
        
        The values of the params are updated according to the
        entries of the configuration contained with in the 
        Configuration object.
        """
        
        for p in params:
            try:    
                params[p] = self.get_config(comp_qualified_name, p)
            except KeyError:
                pass
        
# _system = [System()]

# def sydsys(sid = 0):
#     return _system[sid]
# 
# def restart_sydsys(sid = 0):
#     _system[sid] = System()

# def NoAssertion(obj): return True

# class RequiredFeature(object):
#     def __init__(self, feature):
#         self.feature = feature
#     def __get__(self, obj, T):
#         return self.result # <-- will request the feature upon first call
#     def __getattr__(self, name):
#         assert name == 'result', "Unexpected attribute request other then 'result'"
#         self.result = self.Request()
#         return self.result
#     def Request(self):
#         if self.feature not in sydsys().comp:
#             sydsys().inst(self.feature, None)
#             
#         return sydsys().comp[self.feature]

def all2kwargs(func, *args, **kwargs):
    arg_names, varargs, varkw, defaults = (
        inspect.getargspec(func))

    params = kwargs
    
    if defaults:
        # Add all the arguments that have a default value to the kwargs
        for name, val in zip(reversed(arg_names), reversed(defaults)):
            if name not in params:
                params[name] = val

    for name, val in zip(arg_names, args):
        params[name] = val

    return params

# def compinit(func):
# 
#     def wrapper(self, name=None, parent=None, *args, **kwargs):
#         
#         if func.__name__ != '__init__':
#             raise Exception('Decorated function must be __init__().')
# 
#         params = all2kwargs(func, self, *args, name=name, parent=parent, **kwargs)
#         if self.__cur_parent_class__ is None:
#             if (parent is not None) and (name is not None):    
#             
#                 parent[name] = self
#                 qname = sep.join([parent.qname, name])
#                 
#                 sydsys()[qname] = self
#                 
#                 sys_conf = sydsys().get_all_attrs(qname)
#                 
#                 for n, v in sys_conf.items():
#                     params[n] = v
#                     
#     #             arg_names, varargs, varkw, defaults = (
#     #                                                    inspect.getargspec(func))
#     #             
#     #             if defaults:
#     #                 for arg_name, _ in zip(reversed(arg_names), reversed(defaults)):
#     #                     setattr(self, arg_name, params[arg_name])
#         
#             self.__cur_parent_class__ = self.__class__
#             
#         self.__cur_parent_class__ = self.__cur_parent_class__.__bases__[0] 
#         self.__cur_parent_class__.__init__(**params)
# 
#         func(**params)
#         
#     return wrapper
