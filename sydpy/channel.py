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
from sydpy.unit import Unit

"""Module that implements the Channel class."""

from sydpy._component import Component

class Channel(Unit):
    """Instances of this class allow the information they carry to be read
    and written in various interfaces (by various protocols)"""
    
    def __init__(self, parent, name):
        self.slaves = []
        self.master = None
        Unit.__init__(self, parent, name)
    
    def __irshift__(self, other):
        self.sink(other)
    
    def sink(self, intf):
        if self.master is not None:
            raise Exception("Can only have one master per channel!")
        
        self.master = intf
        intf._mch = self
    
    def __ilshift__(self, other):
        self.drive(other)
    
    def drive(self, intf):
        self.slaves.append(intf)
        intf._sch = self

