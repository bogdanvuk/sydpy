
class SymNodeMeta(type):
    __ignore__ = ("__class__", "__mro__", "__new__", "__init__", 
                "__setattr__", "__getattr__", "__getattribute__",
                "__call__", "__repr__", "__iter__", "__next__", "__weakref__",
                "__subclasshook__", "__module__", "__getnewargs__", "__format__")
    
    _cls = None
    
    def __new__(mcls, name, bases, classdict):  # @NoSelf
         
        def make_proxy(name):
            def proxy(self, *args, **kwargs):
                return mcls._cls(self, name, *args, **kwargs)
            return proxy
        
        if mcls._cls is None:
         
            for mem_name in dir(int):
                if mem_name.startswith("__"):
                    if mem_name not in mcls.__ignore__ and mem_name not in classdict:
                        classdict[mem_name] = make_proxy(mem_name)
         
            cls = type.__new__(mcls, name, bases, classdict)
            
#             for name in dir(int):
#                 if name.startswith("__"):
#                     if name not in mcls.__ignore__ and name not in classdict:
#                         setattr(cls, name, make_proxy(name))
                    
            mcls._cls = cls
                     
        return mcls._cls


class SymNodeVisitor(object):
    
    def visit_node(self, node):
        self.visit(node.elem)
        for a in node.args:
            self.visit(a)
            
    def visit_leaf(self, leaf):
        pass
    
    def visit(self, node):
        if isinstance(node, SymNode):
            self.visit_node(node)
        else:
            self.visit_leaf(node)

class SymNode(object, metaclass=SymNodeMeta):
    def __init__(self, elem, oper, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.oper = oper
        self.elem = elem

    def read(self):
        
        args = []
        
        for a in self.args:
            try:
                args.append(a.read())
            except AttributeError:
                try:
                    args.append(a.eval())
                except AttributeError:
                    args.append(a)
                
        kwargs = {}
        
        for k,v in self.kwargs.items():
            try:
                kwargs[k] = v.read()
            except AttributeError:
                try:
                    kwargs[k] = v.eval()
                except AttributeError:
                    kwargs[k] = v
                
        try:
            elem = self.elem.read()
        except AttributeError:
            try:
                elem = self.elem.eval()
            except AttributeError:
                elem = self.elem
        
        return getattr(elem, self.oper)(*args, **kwargs)