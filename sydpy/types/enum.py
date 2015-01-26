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

"""Module that implements enum sydpy type."""

__struct_classes = {}

from ._type_base import TypeBase

def Enum(*args):
    if args not in __struct_classes:
        __struct_classes[args] = type('enum', (enum,), dict(vals=args))
        
    return __struct_classes[args]

class enum(TypeBase):
    
    vals = None
    
    def __init__(self, val=None):
        if val is None:
            self._val = None
        elif isinstance(val, str):
            for i, v in enumerate(self.vals):
                if v == val:
                    self._val = i
                    return
            else:
                raise Exception("Supplied value not among enum members!")
        else:
            try:
                self._val = int(val._val)
            except AttributeError:
                try:
                    self._val = int(val)
                except TypeError:
                    raise Exception("Cannot convert to enum!")
        
    @classmethod
    def _rnd(cls, rnd_gen):
        val = rnd_gen._rnd_int(0, len(cls.vals))
        
        return cls(val)
    
    def __str__(self):
        if self._val is not None:
            return self.vals[self._val]
        else:
            return ''
    
    __repr__ = __str__
    
    def __int__(self):
        return self._val
    
    def __eq__(self, other):
        if isinstance(other, str):
            if self._val is None:
                return False
            else:
                return self.vals[self._val] == other
        else:
            try:
                for v in other:
                    if self == v:
                        return True
                    
                return False
            except TypeError:
                return self._val == other
        

    