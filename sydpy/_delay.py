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

"""Module implements Delay class"""

from sydpy._simulator import simdelay_add, simdelay_pop

class Delay(object):
    """Class to model delay events."""
    def unsubscribe(self, obj):
        simdelay_pop(obj)
        
    def subscribe(self, obj):
        simdelay_add(obj, self._time)

    def toVerilog(self):
        return "#{0}".format(self._time)

    def __init__(self, val):
        """Return a delay instance.

        Required parameters:
        val -- a natural integer representing the desired delay
        """
        self._time = val
