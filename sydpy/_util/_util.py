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

""" Module with utilility objects.

"""

import time                                                

def timeit(method):
    """ Decorator for function execution timing """
    
    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print('%r (%r, %r) %2.2f sec' % (method.__name__, args, kw, te-ts))
        return result

    return timed

def factory(cls, *args, **kwargs):
    """Instatiate class given by path string
    
    The format expected of the class path is:
    path.to.the.module.ClassName
    """
    class_path_partition = cls.rpartition('.')
    
    class_name = class_path_partition[-1]
    module_name = class_path_partition[0]
    
    if not module_name:
        module_name = "sydpy"
    
    module = __import__(module_name, fromlist=[class_name])
    class_ = getattr(module, class_name)
    
    return class_(*args, **kwargs)

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
    
    