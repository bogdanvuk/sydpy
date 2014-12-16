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

__version__ = "0.1.0a1"

from enum import Enum

class Hdlang(Enum):
    Verilog = 1
    VHDL    = 2
    SystemC = 3

from sydpy._simulator import Simulator
from sydpy._process import always
from sydpy._module import Module, architecture
from sydpy._delay import Delay
from sydpy.procs import clkinst
    
__all__ = ["Simulator",
           "Module",
           "architecture",
           "always",
           "Delay"
           ]
