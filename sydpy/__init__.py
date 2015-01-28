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

__version__ = "0.0.1"

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
from sydpy.intfs import *
from sydpy._delay import Delay
from sydpy.rnd import rnd
from sydpy.types import *
from sydpy._module import Module
from sydpy._util._util import arch, arch_def
from sydpy.procs import Clocking
from sydpy.verif import *
from sydpy.extens import *
    
__all__ = ["Simulator",
           "Module",
           "arch",
           "arch_def",
           "always",
           "always_acquire",
           "always_comb",
           "Delay",
           "Clocking",
           "BasicRndSeq", 
           "BasicSeq", 
           "Sequencer",
           "Scoreboard",
           "UnitTest",
           "sig",
           "seq",
           "tlm",
           "subintfs",
           "Bit",
           "bit",
           "bit8",
           "bit16",
           "bit32",
           "bit64",
           "Array",
           "Enum",
           "Struct",
           "Vector",
           "convgen",
           "conv",
           "VCDTracer",
           "SimtimeProgress"
           ]
