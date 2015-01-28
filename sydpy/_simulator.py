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

"""Module that implements the simulator kernel."""
    
import os
import inspect

from sydpy._util._injector import features, RequiredVariable  # @UnresolvedImport
from sydpy._util._util import class_load, unif_enum, factory
from sydpy._configurator import Configurator

from greenlet import greenlet

def simwait(events=None):
    """Delay process execution by waiting for events."""
    sim = RequiredVariable('Simulator')
    sim.wait(events)
    
def simtime():
    """Get the current simulation time."""
    sim = RequiredVariable('Simulator')
    return sim.time

def simupdate(sig):
    """Register signal for update cycle."""
    sim = RequiredVariable('Simulator')
    sim.update_pool.add(sig)
    
def simtrig(event):
    """Register event to trigger pool."""
    sim = RequiredVariable('Simulator')
    sim.trig_pool.add(event)
    
def simdelay_add(proc, time):
    """Register process to be scheduled for execution after given time."""
    sim = RequiredVariable('Simulator')
    sim.delay_pool[proc] = time + sim.time
    
def simdelay_pop(proc):
    """Remove process from the delay schedule."""
    sim = RequiredVariable('Simulator')
    sim.delay_pool.pop(proc, None)
    
def simproc_reg(proc):
    """Register a process with the simulator."""
    sim = RequiredVariable('Simulator')
    sim.proc_reg(proc)
    
def simarch_inst_start():
    """Mark globaly that the simulator is instantiating an architecture at the moment.
    
    This flag is removed by calling simarch_inst_stop() function.
    """
    sim = RequiredVariable('Simulator')
    sim.arch_inst += 1
    
def simarch_inst_stop():
    """Remove the flag set by simarch_inst_start() function."""
    
    sim = RequiredVariable('Simulator')
    if sim.arch_inst > 0:
        sim.arch_inst -= 1
    
def simarch_inst():
    """Return 0 if no architectures are instantiated right now. Return anything
     else otherwise"""
    
    sim = RequiredVariable('Simulator')
    return (sim.arch_inst > 0)
   
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

class Scheduler(greenlet):
    """Simulator scheduler kernel greenlet wrapper"""
    def run(self, duration = 0, quiet = 0):
        self.simulator._run(duration, quiet)
    
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
    
    def __str__(self):
        return self.name
    
    def __repr__(self):
        return self.__str__()
    
    def __init__(self, sim):
        self.simulator = sim
        self.name = 'Scheduler'
        
        greenlet.__init__(self)
        
        configurator = RequiredVariable('Configurator')
        
        if configurator['sys.scheduler', 'log_task_switching', False]:
            self.settrace(self.callback)

class Simulator(object):
    '''Simulator kernel.'''
    
    def proc_reg(self, proc):
        """Register a process with simulator kernel."""
        self._ready_pool.add(proc)
        self._proc_pool.append(proc)
            
    def __init__(self, config={}):
        '''Create a new Simulator object.'''
        self.time = 0
        self.running = False
        self._finished = False
        self._cosim = None
        self._config = config
        self.arch_inst = 0
        
        # Create events for Simulator extensions to hook to.
        self.events = {
                       'init_start'     : SimEvent(),
                       'run_start'      : SimEvent(),
                       'run_end'        : SimEvent(),
                       'delta_start'    : SimEvent(),
                       'post_evaluate'  : SimEvent(),
                       'delta_end'      : SimEvent(),
                       'timestep_start' : SimEvent(),
                       'timestep_end'   : SimEvent(),
                       }
        
        features.Provide('Simulator', self)
        
        # Create a configurator object from the simulator configuration dictionary
        self._configurator = Configurator(self._config)
        features.Provide('Configurator', self._configurator)

        self.duration = self._configurator['sys.sim', 'duration', 1000]
        self.max_delta_count = self._configurator['sys.sim', 'max_delta_count', 1000]

        # Retreive the top module class. If it is given by string, load the module dynamically           
        self.top_module_cls = class_load(self._configurator['sys', 'top', None]) 
        
        # Either get the project path from the configuration or deduce it by top module file location
        try:
            self._prj_path = self._configurator['sys', 'project_path']
        except KeyError:
            self._prj_path = os.path.dirname(inspect.getfile(self.top_module_cls))
            if not self._prj_path:
                self._prj_path = '.'
                
            self._configurator['sys', 'project_path'] = self._prj_path

        # Change to project_path dir in order for other paths that are specified relatively to work
        self._saved_path = os.getcwd()        
        os.chdir(self._prj_path)
          
        # Instantiate extension classes        
        self.extension_names = self._configurator['sys', 'extensions', []]
        self.extensions = []
        
        for e in self.extension_names:
            self.extensions.append(factory(e, self.events))
            
        self.top_module_name = 'top'
        self.sched = Scheduler(self)
        self.events['init_start'](self)

    def __del__(self):
        os.chdir(self._saved_path)

    def wait(self, events = None):
        """Delay process execution by waiting for events."""
        self.sched.switch(events)

    def run(self):
        self.sched.switch(self.duration)
#     @timeit
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
        self.delay_pool = {}
        self.trig_pool = set()
        self.update_pool = set()     
        self._ready_pool = set()
        self._proc_pool = []

        self.top_module = self.top_module_cls('top', None)

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
