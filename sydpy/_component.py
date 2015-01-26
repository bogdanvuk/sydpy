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

"""Module that implements the Component class.

Component              -- class is the base class for all objects that are 
part of the user object hierarchy.

GlobconfComponentMeta  -- metaclass ensures that all initialization arguments,
for all classes that derive from Component, are updated according to the
Configurator global configuration.

component_visitor      -- Generator for traversing hierarchy of components
"""

import inspect
from sydpy._util._injector import RequiredVariable
from sydpy._util._util import factory

class GlobconfComponentMeta(type):
    """GlobconfComponentMeta metaclass ensures that all initialization arguments,
    for all classes that derive from Component, are updated according to the
    Configurator global configuration.
    """
    def __call__(cls, name, parent, *args, **kwargs):  # @NoSelf
        
        # Derive the hierarhical qualified_name of the component
        if parent is not None:
            qualified_name = parent.qualified_name + '/' + name
        else:
            qualified_name = '/' + name

        
        # Get the initialization arguments
        p = inspect.getargspec(cls.__init__)
        
        initializers = p[0]
        defaults = p[3]
        
        if defaults:
            # Add all the arguments that have a default value to the kwargs
            for arg in zip(reversed(initializers), reversed(defaults)):
                if arg[0] not in kwargs:
                    kwargs[arg[0]] = arg[1]
        
        try:
            configurator = RequiredVariable('Configurator')
            # Update the dictionary of passed arguments 
            configurator.update_config(qualified_name, kwargs)
        except KeyError:
            pass
        
        obj = cls.__new__(cls)
        
        obj.qualified_name = qualified_name
        
        obj.__init__(name, parent, **kwargs)
        
        return obj

class Component(object, metaclass=GlobconfComponentMeta):
    """Component class is the base class for all objects that are part of the user 
    object hierarchy.    
    """
    
    def __init__(self, name, parent):
        """Instantiate a new component
        
        name    -- The name of the new component
        parent  -- The reference to the parent component
        """
        self.parent = parent
        self.name = name
        
        self.components = {}
        
        if parent is not None:
            parent.add(self)
            
    def __repr__(self):
        return self.qualified_name
    
    def inst(self, cls, name=None, **config):
        """Create a new subcomponent.
        
        cls     -- A class object, or a string representing a path to the class
                    path.to.the.class.ClassName
        name    -- Name of the subcomponent 
        
        Reference to this Component object is automatically passes.
        """
        if isinstance(cls, str):
            if name is None:
                name = cls
                
            comp = factory(cls)(name, self, **config)
        else:
            if name is None:
                name = cls.__name__
                
            comp = cls(name, self, **config)

        return comp
            
    def add(self, comp):
        """Add a new subcomponent to the component dictionary."""
        self.components[comp.name] = comp
    
    def find(self, qualified_name):
        """Retreive the component from the hierarchy by its qualified name
        
        Required arguments:
            qualified_name    - The qualified name of component to find
            
        Return values:
            (comp, path)      - Either the found component and empty string, or
                                the component furthest down the path and the
                                remaining of the path that could not be traced
        """
        if qualified_name[0] == '/':
            if self.parent is not None:
                return self.parent.find(qualified_name)
            else:
                return self.find(qualified_name[1:])
        elif qualified_name[0:3] == '../':
            return self.parent.find(qualified_name[3:])
        elif qualified_name[0:2] == './':
            return self.find(qualified_name[2:])
        else:
            slash_pos = qualified_name.find('/')

            if slash_pos == -1:
                if qualified_name not in self.components:
                    return (self, qualified_name)                
                else:
                    return (self.components[qualified_name], '')
            else:
                comp_name = qualified_name[:slash_pos-1]
                rest_path = qualified_name[slash_pos+1:]

                if comp_name not in self.components:
                    return (self, qualified_name)                
                else:
                    return self.components[comp_name].find(rest_path)

    def __getattr__(self, name):
        if name in self.components:
            return self.components[name]
        else:
            raise AttributeError
        
    def __getitem__(self, key):
        return self.components[key]
        
def component_visitor(top, before_comp=None, mid_comp=None, mid_comp_post=None, end_comp=None):
    """Visits all components from the hierarchy and calls supplied callbacks."""
    _component_visitor_re(top, before_comp, mid_comp, mid_comp_post, end_comp)
    
def _component_visitor_re(container, before_comp=None, mid_comp=None, mid_comp_post=None, end_comp=None):
    if before_comp:
        before_comp(container)
        
    if (isinstance(container, (Component, tuple, list))):
        for c in container.components:
            if mid_comp:
                mid_comp(container, container.components[c])
            _component_visitor_re(container.components[c], before_comp, mid_comp, mid_comp_post, end_comp)
            if mid_comp_post:
                mid_comp_post(container, container.components[c])
            
    if end_comp:
        end_comp(container)             