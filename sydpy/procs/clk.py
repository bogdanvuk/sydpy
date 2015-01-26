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

"""Module implements the Clocking helper module."""

from sydpy import arch_def, Delay, always, Module
from sydpy.types import bit
from sydpy.intfs import sig
from sydpy._util.decorator import decorator

def clkinst(period=100, name='clk'): #period=100
    @decorator
    def wrapper(f, *args, **kwargs):
        args[0].inst(Clocking, name + "_proc", clk_o=name, period=period)
        
        if f is not None:
            return f(*args, **kwargs)
        
    return wrapper
        
class Clocking(Module):
    @arch_def
    def rtl(self, 
            clk_o   : sig(bit).master, 
            period  = 100):
        
        clk_o.next = 0
        
        @always(self, Delay(int(period/2)))
        def produce():
            clk_o.next = ~clk_o