import fnmatch
import inspect
import re
# from sydpy.sydpy import system

class System(object):
    
    def __init__(self):
        self._conf = {}
        self.providers = {}
        self.index = {}
       
    def __getitem__(self, path):
        if path not in self.index:
            attr_name = path.split('.', 1)[0]
            val = self.get_config('', attr_name)
            setattr(self, attr_name, val(attr_name))
            
        return self.index[path]
    
    def __setitem__(self, path, val):
        self.index[path] = val

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

    def findall(self, pattern='*', of_type=None):
#         self.update_index()
        comps = {}
        for k in fnmatch.filter(self.index.keys(), pattern):
            comp = self.index[k]
            if (of_type is None) or (isinstance(comp, of_type)):
                comps[k] = comp
                 
        return comps

    def set_config(self, config):
        self.config = config
        params = self.get_all_attrs('')
        for p,v in params.items():
            if p not in self.index:
                setattr(self, p, v(p))
    
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
        
system = System()

def NoAssertion(obj): return True

class RequiredFeature(object):
    def __init__(self, feature):
        self.feature = feature
    def __get__(self, obj, T):
        return self.result # <-- will request the feature upon first call
    def __getattr__(self, name):
        assert name == 'result', "Unexpected attribute request other then 'result'"
        self.result = self.Request()
        return self.result
    def Request(self):
        return system[self.feature]

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

def compinit(func):

    def wrapper(self, name, *args, **kwargs):
    
        if func.__name__ != '__init__':
            raise Exception('Decorated function must be __init__().')
        
        system[name] = self
        
        sys_conf = system.get_all_attrs(name)
        
        params = all2kwargs(func, self, *args, name=name, **kwargs)
        
        for name, val in sys_conf.items():
            params[name] = val
            
        arg_names, varargs, varkw, defaults = (
                                               inspect.getargspec(func))
        
        if defaults:
            for arg_name, _ in zip(reversed(arg_names), reversed(defaults)):
                setattr(self, arg_name, params[arg_name])
    
        self.__class__.__bases__[0].__init__(**params)

        func(**params)
        
    return wrapper

class Component(object):
    """Component class is the base class for all objects that are part of the user 
    object hierarchy.    
    """
    
    def __init__(self, name, **kwargs):
        """Instantiate a new compinit
        
        name    -- The name of the compinit
        """

        self.name = name

    def __repr__(self):
        return self.name

    def inst(self, name, cls, *args, **kwargs):
        try:
            val = system.get_config(self.name, name)
            if not inspect.isclass(val):
                setattr(self, name, val)
                return val
            else:
                cls = val
        except KeyError: 
            pass
        
        obj = cls(self.name + '.' + name, *args , **kwargs)
        setattr(self, name, obj)
        
        return obj
        
#     @property
#     def qualified_name(self):
#         if self._parent:
#             parent_qualified_name = self._parent.qualified_name
#             
#             if parent_qualified_name == '/':
#                 parent_qualified_name = '' 
#         
#             return parent_qualified_name + '/' + self.name        
#         else:
#             return '/'
# 
#     def find(self, qualified_name):
#         """Retreive the compinit from the hierarchy by its qualified name
#         
#         Required arguments:
#             qualified_name    - The qualified name of compinit to find
#             
#         Return values:
#             (comp, path)      - Either the found compinit and empty string, or
#                                 the compinit furthest down the path and the
#                                 remaining of the path that could not be traced
#         """
#         if not qualified_name:
#             return self
#         elif qualified_name[0] == '/':
#             if self._parent is not None:
#                 return self._parent.find(qualified_name)
#             else:
#                 return self.find(qualified_name[1:])
#         elif qualified_name[0:3] == '../':
#             return self._parent.find(qualified_name[3:])
#         elif qualified_name[0:2] == './':
#             return self.find(qualified_name[2:])
#         else:
#             segments = qualified_name.split('/', 1)
# 
#             compinit = self.components[segments[0]]
#             if len(segments) > 1:
#                 return compinit.find(segments[-1])
#             else:
#                 return compinit
#             
#     def findall(self, pattern='*', of_type=None):
#         comps = {}
#         for k in fnmatch.filter(self.index().keys(), pattern):
#             comp = self.find(k)
#             if (of_type is None) or (isinstance(comp, of_type)):
#                 comps[k] = comp
#                 
#         return comps
#     
#     def __getitem__(self, key):
#         return self.find(key)
#     
#     def __contains__(self, key):
#         try:
#             self.find(key)
#             return True
#         except (KeyError, IndexError):
#             return False
# 
#     def index(self):
#         index = {self.qualified_name: self}
#         
#         for comp in self.components:
#             index.update(self.components[comp].index())
#             
#         return index
#     
#     def __getattr__(self, name):
#         if name in self.components:
#             return self.components[name]
#         else:
#             raise AttributeError
#    
#     __iadd__ = add

# class Counter(Component):
# 
#     def init(self, cin, cout):
#         self.add("cin", iseq(bit8))
#         cin.add(self.cin.slv)
#         
#         self.add("cout", isig(bit8))
#         cout.add(self.cout.mst)
# 
#     def process(self):
#         self.cout <<= self.cin + 1
