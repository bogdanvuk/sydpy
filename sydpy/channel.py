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

"""Module that implements the Channel class."""

from sydpy.component import Component, compinit

class Channel(Component):
    """Instances of this class allow the information they carry to be read
    and written in various interfaces (by various protocols)"""

    @compinit    
    def __init__(self, **kwargs):
        self.slaves = []
        self.master = None
        self.master_connected = False
    
    def __irshift__(self, other):
        self.drive(other)
        return self
    
    def sink(self, intf):
        if self.master is not None:
            raise Exception("Can only have one master per channel!")
        
        self.master = intf
        self.master_connected = True
        intf._drive(self)
        
        for s in self.slaves:
            s._connect()
        
#         self._gen_drivers()
#         intf._mch = self
    
    def __ilshift__(self, other):
        self.sink(other)
        return self
    
    def drive(self, intf):
        self.slaves.append(intf)
        intf._sink(self)

        if self.master_connected:
            intf._connect()
#         intf._sch = self

