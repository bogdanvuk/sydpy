from sydpy.component import Component
from sydpy.unit import Unit
from sydpy._util._util import class_load, unif_enum

from greenlet import greenlet
from sydpy.process import Process

class Scheduler(Unit, greenlet):
    """Simulator scheduler kernel greenlet wrapper"""
    
    def __init__(self, sim):
        greenlet.__init__(self)
        self.log_task_switching = False
        self.sim = sim
        Unit.__init__(self, sim, "sched")
    
    def run(self, duration = 0, quiet = 0):
        self.sim._run(duration, quiet)

    def build(self):        
        if self.log_task_switching:
            self.settrace(self.callback)
    
    def callback(self, event, args):
        """Callback that monitors process switching for debuggin purposes"""
        if event == 'switch':
            origin, target = args
            if target == self:
                if hasattr(origin, 'events'):
                    print("Process {0} run, and waits for: ".format(origin, origin.events))
            return
        if event == 'throw':
            origin, target = args
            print("I Threw!")
            return
            
class Simulator(Unit):
    '''Simulator kernel.'''

    def __init__(self, parent):
        Unit.__init__(self, parent, "sim")

    def build(self):
        if hasattr(self, 'top'):
            self.top = class_load(self.top)(self._parent, 'top')
        
        self.add(Scheduler(self))
    
    def gen_drivers(self):
        for _, comp in self.top.index().items():
            if hasattr(comp, '_gen_drivers'):
                comp._gen_drivers()
    
    def run(self):
        self.sched.switch(self.duration)
   
    def _run(self, duration=0, quiet=0):
        """Start the simulator scheduler loop."""
        
        # Instantiate the user module hierarchy
        self._initialize()
        
        if duration:
            self.duration = duration
        
#         self.max_time = self.time + self.duration
# 
#         self.events['run_start'](self)
#         self.running = True
#         
#         while 1:
#             self.delta_count = 0
#             self.events['timestep_start'](self.time, self)
#             # Perform delta cycle loop as long as the events are triggering
#             while self._ready_pool or self.trig_pool:
#                 #Perform one delta cycle
#                 self.events['delta_start'](self.time, self.delta_count, self)
#                 
#                 self._evaluate()
#                 
#                 self.events['post_evaluate'](self.time, self.delta_count, self)
#                 
#                 self._update()
#                 
#                 self.events['delta_end'](self.time, self.delta_count, self)
#                 
#                 self.delta_count += 1
#                 
#                 if self.delta_count > self.max_delta_count:
#                     self._finalize()
#                     self.events['run_end'](self)
#                     self._finished = True
#                     raise Exception("Maximum number of delta cycles reached: {0}".format(self.max_delta_count))
#                 
# #                 print('-----------------------------------------')
#                 
#             self.events['timestep_end'](self.time, self)
#             
#             # All events have settled, let's advance time
#             if not self._advance_time():
#                 self._finalize()
#                 self.events['run_end'](self)
#                 self._finished = True
#                 raise greenlet.GreenletExit 
    
    def _initialize(self):
        
        self.max_time = None
        self.delay_pool = {}
        self.trig_pool = set()
        self.update_pool = set()     
        self._ready_pool = set()
        self._proc_pool = []
        
        procs = self.top.findall(of_type=Process)
        for qname, proc in procs.items():
            self.proc_reg(proc)
        
        self.gen_drivers()
#         self.top_module = self.top_module_cls('top', None)

    def _unsubscribe(self, proc):
        """Unsubscribe the process from all events from  its sensitivity list."""
        
        events = getattr(proc, 'events', None)
        if events:
            for e in unif_enum(events):
                try:
                    e.unsubscribe(proc)
                except:
                    e.event_def.unsubscribe(proc)
    
    def _subscribe(self, proc, events):
        """Subscribe the process to all events from  its sensitivity list."""
        
        proc.events = events
        
        for e in unif_enum(events):
            try:
                e.subscribe(proc)
            except AttributeError:
                e.subscribe(proc)
                e.event_def.subscribe(proc)
   
    def _evaluate(self):
        """Run all processes scheduled for execution. Resolve all triggered events afterwards."""
         
        # Run the ready processes
        while self._ready_pool:
            proc = self._ready_pool.pop()
            self._unsubscribe(proc)
            events = proc.switch()

            if events is not None:
                self._subscribe(proc, events)
            else:
                # If process supplied no waiting events, it is to be terminated
                self._proc_pool.remove(proc)
                proc.exit_func()
        
        # Resolve all triggered events          
        while self.trig_pool:
            trig = self.trig_pool.pop()
            trig.resolve(self._ready_pool)

    def _update(self):
        """Ask all signals to _update their values, and trigger new events. """
        
        for s in self.update_pool:
            s._update()
            
        self.update_pool.clear()
        
    def _advance_time(self):
        """Advanced time to the earliest scheduled process in delay pool and 
        return True, or return False if there are no more scheduled processes"""
        
        if self.delay_pool:
            t_new = None
            
            while self.delay_pool:
                w = min(self.delay_pool, key=self.delay_pool.get)
                if not t_new:
                    t_new = self.delay_pool[w]
                elif self.delay_pool[w] > t_new:
                    break
                    
                self.delay_pool.pop(w)
                self._ready_pool.add(w)

            self.time = t_new
            self.delta_count = 0
            
            if self.time > self.max_time:
                return False
            else:
                return True
        else:
            return False
        
    def _finalize(self):
        """Call the exit functions of all processes."""
        
        for p in self._proc_pool:
            p.exit_func()
            
        self._finished = True

    def proc_reg(self, proc):
        """Register a process with simulator kernel."""
        self._ready_pool.add(proc)
        self._proc_pool.append(proc)
    
    def wait(self, events = None):
        """Delay process execution by waiting for events."""
        self.sched.switch(events)
    
#     def apply_