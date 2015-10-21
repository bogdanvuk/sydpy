import fnmatch

class Component(object):
    """Component class is the base class for all objects that are part of the user 
    object hierarchy.    
    """
    
    def __init__(self, name):
        """Instantiate a new component
        
        name    -- The name of the component
        """

        self._parent = None
        self.name = name
        
        self.components = {}

    def __repr__(self):
        return self.qualified_name

    def add(self, comp):
        self.components[comp.name] = comp
        comp._parent = self
        return self
    
    @property
    def qualified_name(self):
        if self._parent:
            parent_qualified_name = self._parent.qualified_name
            
            if parent_qualified_name == '/':
                parent_qualified_name = '' 
        
            return parent_qualified_name + '/' + self.name        
        else:
            return '/'

    def find(self, qualified_name):
        """Retreive the component from the hierarchy by its qualified name
        
        Required arguments:
            qualified_name    - The qualified name of component to find
            
        Return values:
            (comp, path)      - Either the found component and empty string, or
                                the component furthest down the path and the
                                remaining of the path that could not be traced
        """
        if not qualified_name:
            return self
        elif qualified_name[0] == '/':
            if self._parent is not None:
                return self._parent.find(qualified_name)
            else:
                return self.find(qualified_name[1:])
        elif qualified_name[0:3] == '../':
            return self._parent.find(qualified_name[3:])
        elif qualified_name[0:2] == './':
            return self.find(qualified_name[2:])
        else:
            segments = qualified_name.split('/', 1)

            component = self.components[segments[0]]
            if len(segments) > 1:
                return component.find(segments[-1])
            else:
                return component
            
    def findall(self, pattern='*', of_type=None):
        comps = {}
        for k in fnmatch.filter(self.index().keys(), pattern):
            comp = self.find(k)
            if (of_type is None) or (isinstance(comp, of_type)):
                comps[k] = comp
                
        return comps
    
    def __getitem__(self, key):
        return self.find(key)
    
    def __contains__(self, key):
        try:
            self.find(key)
            return True
        except (KeyError, IndexError):
            return False

    def index(self):
        index = {self.qualified_name: self}
        
        for comp in self.components:
            index.update(self.components[comp].index())
            
        return index
    
    def __getattr__(self, name):
        if name in self.components:
            return self.components[name]
        else:
            raise AttributeError
   
    __iadd__ = add

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