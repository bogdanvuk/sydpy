from sydpy.component import Component, compinit, RequiredFeature, system
from sydpy.unit import Unit
from sydpy._util._util import class_load, unif_enum

from greenlet import greenlet
from sydpy.process import Process
from sydpy._util._injector import features
from sydpy.intfs.intf import Intf

class SimEvent(list):
    """Simulator Event that can trigger list of callbacks.

    Event is implemented as a list of callable objects - callbacks. 
    Calling an instance of this will cause a call to each item in 
    the list in ascending order by index.
    
    Callback function should return a boolean value. If it returns:
    
    True    -- Callback is re-registered by the _event
    False   -- Callback is deleted from the list     
    
    Callback can be registered with or without arguments. Callback
    without arguments is registered by adding function reference
    to the list. Callback with arguments is registered by adding
    a tuple to the list. The first tuple item contains function 
    reference. The rest of the items will be passed to the
    callback once the _event is triggered.
    """
    def __call__(self, *args, **kwargs):
        """Trigger the _event and call the callbacks.
        
        The arguments passed to this function will be passed to 
        all the callbacks.
        """
        
        expired = []
        
        for i, f in enumerate(self):
            # If additional callback arguments are passed
            if isinstance(f, tuple):
                func = f[0]
                fargs = f[1:]
                
                ret = func(*(fargs + args), **kwargs)
            else:
                ret = f(*args, **kwargs)
            
            # If callback should not be re-registered
            if not ret:
                expired.append(i)
    
        # Delete from the list all callback that returned false
        for e in reversed(expired):
            del self[e]
        

    def __repr__(self):
        return "Event(%s)" % list.__repr__(self)

class Scheduler(Component, greenlet):
    """Simulator scheduler kernel greenlet wrapper"""
    
    sim = RequiredFeature('sim')
    
    @compinit
    def __init__(self, log_task_switching = False, **kwargs):
        greenlet.__init__(self)
    
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
            
class Simulator(Component):
    '''Simulator kernel.'''

    @compinit
    def __init__(self, top=None, duration = 0, max_delta_count=1000, **kwargs):
        self.delay_pool = {}
        self.trig_pool = set()
        self.update_pool = set()     
        self._ready_pool = set()
        self._proc_pool = []

        # Create events for Simulator extensions to hook to.
        self.events = {
                       'init_start'     : SimEvent(),
                       'run_start'      : SimEvent(),
                       'run_end'        : SimEvent(),
                       'delta_start'    : SimEvent(),
                       'post_evaluate'  : SimEvent(),
                       'delta_end'      : SimEvent(),
                       'delta_settled'  : SimEvent(),
                       'timestep_start' : SimEvent(),
                       'timestep_end'   : SimEvent(),
                       }
        
#         self.inst('top', class_load(top))
        self.inst('sched', Scheduler)

        #         Unit.__init__(self, parent, "sim")
    
    def gen_drivers(self):
        for _, comp in system.findall(self.name + '.top*').items():
            if hasattr(comp, '_gen_drivers'):
                comp._gen_drivers()

#     def find_sources(self):
#         finished_all = True
#         for comp in system.search(self.name + '.top*', of_type=Intf).items():
# #         for _, comp in system.findall(self.name + '.top*').items():
#             if hasattr(comp, '_find_sources'):
#                 finished = comp._find_sources()
#                 if not finished:
#                     finished_all = False
#                     
#         return finished_all
    
    def run(self):
        self.sched.switch(self.duration)
   
    def _run(self, duration=0, quiet=0):
        """Start the simulator scheduler loop."""
        
        # Instantiate the user module hierarchy
        self._initialize()
        
        if duration:
            self.duration = duration
        
        self.max_time = self.time + self.duration
 
        self.events['run_start'](self)
        self.running = True
         
        while 1:
            self.delta_count = 0
            self.events['timestep_start'](self.time, self)
            # Perform delta cycle loop as long as the events are triggering
            while self._ready_pool or self.trig_pool:
                #Perform one delta cycle
                self.events['delta_start'](self.time, self.delta_count, self)
                 
                self._evaluate()
                 
                self.events['post_evaluate'](self.time, self.delta_count, self)
                 
                self._update()
                 
                self.events['delta_end'](self.time, self.delta_count, self)
                 
                self.delta_count += 1
                 
                if self.delta_count > self.max_delta_count:
                    self._finalize()
                    self.events['run_end'](self)
                    self._finished = True
                    raise Exception("Maximum number of delta cycles reached: {0}".format(self.max_delta_count))
                
                if not (self._ready_pool or self.trig_pool):
                    self.events['delta_settled'](self)
                
#                 print('-----------------------------------------')
                 
            self.events['timestep_end'](self.time, self)
             
            # All events have settled, let's advance time
            if not self._advance_time():
                self._finalize()
                self.events['run_end'](self)
                self._finished = True
                raise greenlet.GreenletExit 
    
    def _initialize(self):
        
        self.max_time = None
        self.time = 0
        
#         self.gen_drivers()
        
#         while (not self.find_sources()):
#             pass
        
#         self.top_module = self.top_module_cls('top', None)

    def _unsubscribe(self, proc):
        """Unsubscribe the process from all events from  its sensitivity list."""
        
        events = getattr(proc, 'events', None)
        if not isinstance(events, set):
            if hasattr(events, '__iter__'):
                events = set([e for e in events])
            elif events is not None:
                events = set([events])
            
        if events:
            for e in events:
                e.unsubscribe(proc)
#                 try:
#                     e.unsubscribe(proc)
#                 except:
#                     raise
#                     e.event_def.unsubscribe(proc)
    
    def _subscribe(self, proc, events):
        """Subscribe the process to all events from  its sensitivity list."""
        
        proc.events = events
        
#         for e in unif_enum(events):
        for e in events:
            e.subscribe(proc)
#             try:
#                 e.subscribe(proc)
#             except AttributeError:
#                 e.subscribe(proc)
#                 e.event_def.subscribe(proc)
   
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
    
    def update (self, sig):
        self.update_pool.add(sig)
    
    def wait(self, events = None):
        """Delay process execution by waiting for events."""
        self.sched.switch(events)
    
    def delay_add(self, proc, time):
        """Register process to be scheduled for execution after given time."""
        self.delay_pool[proc] = time + self.time
    
    def delay_pop(self,proc):
        """Remove process from the delay schedule."""
        self.delay_pool.pop(proc, None)

    def trigger(self, event):
        """Register event to trigger pool."""
        self.trig_pool.add(event)

    
#     def apply_