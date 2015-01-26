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

from sydpy._component import Component
from sydpy.intfs._intf import IntfDir

class Channel(Component):
    """Instances of this class allow the information they carry to be read
    and written in various interfaces (by various protocols)"""
    
    def __init__(self, name, parent, trace = True):
        self.slaves = []
        self.master = None
        self.traces = []
        self._tracing = trace
        Component.__init__(self, name, parent)
    
    def register_traces(self, traces):
        if self._tracing:
            self.traces.extend(traces)
    
    def register_proxy(self, proxy):
        if proxy.side == IntfDir.slave:
            self.slaves.append(proxy)
            
            if self.master is not None:
                proxy.conn_to_intf(self.master)
        else:
            if self.master is not None:
                raise Exception("Can only have one master per channel!")
            
            self.master = proxy
            
            for slave in self.slaves:
                if not slave.is_sourced():
                    slave.conn_to_intf(self.master)
                    