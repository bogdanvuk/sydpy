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

from sydpy import ConversionError

class Intf(object):
    
    def __init__(self, parent=None, name=''):
        self.parent = parent
        self.name = name
        self.def_subintf = None
        self.subintfs = {}

    def _intf_parents_eq(self, val):
        parent = self.parent
        val_parent = val.parent
        
        try:
            while (parent is not None) or (val_parent is not None):
                if parent != val_parent:
                    return False
            
                parent = parent.parent
                val_parent = val_parent.parent
            
        except AttributeError:
            return False
        
        return True
    
    def conv_path(self, val):
        
        if self._intf_parents_eq(val) and (self.name == val.name):
            try:
                yield from getattr(self, '_from_' + val.__class__.__name__)(val)
            except AttributeError:
                yield from getattr(val, '_to_' + self.__class__.__name__)(self)
                
        return
    
    def __eq__(self, other):
        try:
            if not (self.subintfs == other.subintfs):
                return False
            
            return self.dtype == other.dtype
        except AttributeError:
            return False
    
    def __hash__(self):
        return type.__hash__(self)
         
    def __getattr__(self, name):
        if name in self.subintfs:
            return self.subintfs[name]
        else:
            raise AttributeError
    
    def _conv_gen_none(self, other, remain):
        yield other
        return remain
    
    def convgen(self, other, remain=None):
        try:
            return self.dtype.convgen(other, remain)
        except AttributeError:
            return self._conv_gen_none(other, remain)
   
    def _conv(self, other):
        try:
            return getattr(self.dtype, '_from_' + other.__class__.__name__)(other)
        except AttributeError:
            try:
                return getattr(other, '_to_' + self.dtype.__name__)(self.dtype)
            except AttributeError:
                raise ConversionError
            
    def _conv_iter(self, other):
        try:
            yield from getattr(self.dtype, '_iter_from_' + other.__class__.__name__)(other)
        except AttributeError:
            try:
                yield from getattr(other, '_iter_to_' + self.dtype.__name__)(self.dtype)
            except AttributeError:
                raise ConversionError
            
    def __call__(self, *args):
        if args:
            try:
                return self.dtype(args[0])
            except TypeError:
                return args[0]
        else:
            try:
                return self.dtype()
            except TypeError:
                return None
            
            