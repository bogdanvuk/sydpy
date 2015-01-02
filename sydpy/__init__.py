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

class ConversionError(Exception):
    def __init__(self, val=None):
        self.val = val

from sydpy._simulator import Simulator, simwait
from sydpy._process import always, always_acquire, always_comb
from sydpy._module import Module
from sydpy._util._util import architecture
from sydpy._delay import Delay
from sydpy.procs import Clocking
from sydpy.rnd import rnd
from sydpy.verif import *
from sydpy.intfs import *
from sydpy.types import *
    
__all__ = ["Simulator",
           "Module",
           "architecture",
           "always",
           "always_acquire",
           "always_comb",
           "Delay",
           "Clocking",
           "BasicRndSeq", 
           "BasicSeq", 
           "Sequencer",
           "Scoreboard",
           "sig",
           "seq",
           "tlm",
           "bit",
           "bit8",
           "bit16",
           "bit32",
           "bit64"
           ]
