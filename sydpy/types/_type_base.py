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

"""Module implements the base type for all sydpy types."""

from sydpy import ConversionError

def conv(val, to_type):
    """Converts a value to specified type."""
    return to_type.conv(val)

def convgen(val, to_type, remain=None):
    """Generator conversion function. It can output multiple converted values 
    from a single source value.
    
    For an example conversion of list of integers to integers.
    """
    
    _convgen = to_type._convgen(val, remain)
    while True:
        data, _remain = next(_convgen)
        
        yield data

class TypeBase(object):
    """Base type for all sydpy typles."""
    
    @classmethod
    def cls_eq(cls, other):
        """Check if the types are of the same class."""
        return object.__eq__(cls, other)
    
    @classmethod
    def _conv_direct(cls, other):
        try:
            return getattr(cls, '_from_' + other.__class__.__name__)(other)
        except AttributeError:
            pass
        
        try:
            return getattr(other, '_to_' + cls.__name__)(cls)
        except AttributeError:
            raise ConversionError
        
    @classmethod
    def conv(cls, other=None):
        """Try to perform a simple conversion: one source to one converted object."""
        try:
            return getattr(cls, '_from_' + other.__class__.__name__)(other)
        except AttributeError:
            pass
        
        try:
            return getattr(other, '_to_' + cls.__name__)(cls)
        except AttributeError:
            pass
        
        try:
            return cls(other)
        except:
            pass
        
        try:
             
            other_vals = list(other)
            data_prep = cls()
             
            for v in other_vals:
                 
                if data_prep._full():
                    raise ConversionError
                 
                data_prep, remain = data_prep._icon(v)
                 
                if data_prep._full():
                    if remain is not None:
                        raise ConversionError
                     
            return data_prep
        
        except AttributeError:
            raise ConversionError
        except TypeError:
            raise ConversionError
        except ConversionError:
            raise ConversionError
    
    @classmethod        
    def convgen(cls, other, remain=None):
        """Generator conversion function. It can output multiple converted values 
        from a single source value.
        
        For an example conversion of list of integers to integers.
        """
    
        _convgen = cls._convgen(other, remain)
        while True:
            data, _remain = next(_convgen)
            
            yield data
    
    @classmethod        
    def _convgen(cls, other, remain=None):
        #First try the direct conversion
        try:
            yield (cls._conv_direct(other), None)
            return None
        except ConversionError:
            pass
        
        #Then try to get the sequence of direct conversions
        try:
            for e in other:
                yield (cls._conv_direct(e), None)
                
            return None
        except TypeError:
            pass
        except ConversionError:
            pass

        #Lastly try concatenation
        try:
            if remain is None:
                data_prep = cls()
            else:
                data_prep = cls(remain)
            
            data_full = False           
            _remain = other
            while _remain is not None:
                data_full = False
                data_prep, _remain = data_prep._icon(_remain)
                if data_prep._full():
                    resp = (yield data_prep, _remain)
                    
                    if resp == False:
                        return _remain
                    
                    data_full = True
                    data_prep = cls()
                    
            if not data_full:
                return data_prep
            else:
                return None
        except TypeError:
            pass
        except ConversionError:
            pass
            
        #Then try to get the sequence of direct conversions
        try:
            
            _remain = remain
            data_prep = None
            
            other_vals = list(other)
            
            if _remain is not None:
                data_prep = cls(_remain)
            elif data_prep is None:    
                data_prep = cls()
            
            while other_vals:
                    
                _remain = other_vals.pop(0)
                while _remain is not None:
                    data_full = False
                    data_prep, _remain = data_prep._icon(_remain)
                    if data_prep._full():
                        if _remain is not None:
                            other_vals = [_remain] + other_vals
                            if not other_vals:
                                other_vals = None
                                
                            _remain = None
                             
                        resp = (yield data_prep, other_vals)
                        
                        if resp == False:
                            return _remain
                        
                        data_prep = cls()
                        data_full = True
                        
            if not data_full:
                return data_prep
            else:
                return None

        except TypeError:
            pass
        except ConversionError:
            pass
        
        #Then try to get the sequence of direct conversions
        try:
            for e in other:
                remain = yield from cls._convgen(e, remain)
            
            return remain
        except TypeError:
            pass
        except ConversionError:
            pass

