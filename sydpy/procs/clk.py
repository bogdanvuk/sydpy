from sydpy import architecture, Delay, always, Module
from sydpy.aspects import bit, sig
from sydpy._util.decorator import decorator

def clkinst(period=100, name='clk'): #period=100
    @decorator
    def wrapper(f, *args, **kwargs):
        args[0].inst(Clocking, name + "_proc", clk_o=name, period=period)
        
        if f is not None:
            return f(*args, **kwargs)
        
    return wrapper
        
class Clocking(Module):
    @architecture
    def rtl(self, 
            clk_o   : sig(bit), 
            period  = 100):
        
        clk_o.next = 0
        
        @always(self, Delay(int(period/2)))
        def produce():
            clk_o.next = ~clk_o