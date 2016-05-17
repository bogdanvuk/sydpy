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
from ddi.ddi import Dependency, ddic
from sydpy.intfs.isig import Isig

"""Module implements VCDTracer simulator extension."""

import time
import os
from sydpy._util._injector import RequiredVariable, features  # @UnresolvedImport
from sydpy import __version__ #, EnumItemType

class VCDTracer:
    def __init__(self, sim: Dependency('sim'),
                 patterns=['*'],
                 vcd_filename='sydpy.vcd', channel_hrchy=True, 
                 vcd_out_path='.', timescale='100ps', trace_deltas=False,
                 ):
        
        self.sim = sim
        self.patterns = patterns
        self.vcd_filename = vcd_filename
        self.channel_hrchy = channel_hrchy
        self.vcd_out_path = vcd_out_path
        self.timescale = timescale
        self.trace_deltas = trace_deltas
        self.max_delta_count = sim.max_delta_count
        
        if (not os.path.isdir(self.vcd_out_path)):
            os.makedirs(self.vcd_out_path, exist_ok=True)
        
        self.vcdfile = open(self.vcd_out_path + "/" + self.vcd_filename + ".tmp", 'w')
        
        self.trace_list = []
        self.last_code = ['a', 'a', 'a']
        sim.events['timestep_start'].append(self.write_timestamp)
        sim.events['timestep_end'].append(self.write_traces)
        sim.events['update'].append(self.signal_update)
        self.trace_list = None
        self.untraced_isigs = None
        self.sig_to_traces_map = {}
        self.updated_signals = set()
        
#         if self.trace_deltas:
#             sim.events['delta_start'].append(self.write_delta_traces)
            
        sim.events['run_end'].append(self.writeVcdHeader)

    def signal_update(self, signal, sim):
        self.updated_signals.add(signal)
        return True 
    
    def _print_val(self):
        if isinstance(self.isig.read(), bool):
            self.vcdfile.write("b{0} {1}\n".format(int(self.isig.read()), self._code))
        elif hasattr(self.isig.read(), 'bitstr'):
            self.vcdfile.write("b{0} {1}\n".format(self.isig.read().bitstr(), self._code))
        else: # default to 'string'
            self.vcdfile.write("s{0} {1}\n".format(str(self.isig.read()).replace(' ', '').replace("'", ""), self._code))

    def create_trace(self, isig):
       
        code =  "".join(self.last_code)
     
        if self.last_code[2] != 'z':
            self.last_code[2] = chr(ord(self.last_code[2]) + 1)
        else:
            if self.last_code[1] != 'z':
                self.last_code[1] = chr(ord(self.last_code[1]) + 1)
                self.last_code[2] = 'a'
            else:
                self.last_code[0] = chr(ord(self.last_code[0]) + 1)
                self.last_code[1] = 'a'
                self.last_code[2] = 'a'
        
        trace = VCDTrace(isig, code=code, vcdfile=self.vcdfile)
             
        return trace
    
    def write_traces(self, time, sim):
        if self.trace_list is None:
            self.untraced_isigs = []
            self.trace_list = []
            
            for p in self.patterns:
                for name in ddic.search(p, lambda obj: isinstance(obj, Isig)):
                    isig = ddic[name]  
                    if isig._sourced:
                        trace = self.create_trace(isig)
                        self.trace_list.append(trace)

                        if isig._sig not in self.sig_to_traces_map:
                            self.sig_to_traces_map[isig._sig] = set()
                             
                        self.sig_to_traces_map[isig._sig].add(trace)
                    else:
                        self.untraced_isigs.append(isig)

#         for t in self.trace_list:
#             if t._sourced and t._sig in self.updated_signals:
#                 t.print_val()
        
        if self.untraced_isigs:
            traced = []
            for i, isig in enumerate(self.untraced_isigs):
                if isig._sourced:
                    traced.append(i)
                    trace = self.create_trace(isig)
                    self.trace_list.append(trace)
                    if isig._sig not in self.sig_to_traces_map:
                        self.sig_to_traces_map[isig._sig] = set() 
                    
                    self.sig_to_traces_map[isig._sig].add(trace)
                    
            for i in reversed(traced):
                del self.untraced_isigs[i]

        for signal in self.updated_signals:
            if signal not in self.sig_to_traces_map:
                traces = set()
                for i in self.untraced_isigs:
                    if signal is i._sig:
                        traces.add(self.create_trace(i))
                 
                self.sig_to_traces_map[signal] = traces
                 
            for trace in self.sig_to_traces_map[signal]:
                trace.print_val()

        self.updated_signals.clear()
        return True
    
    def writeVcdHeader(self, sim):
        self.vcdfile.close()
        self.vcdfile = open(self.vcd_out_path + "/" + self.vcd_filename, 'w')
         
        self.used_codes = set()
         
        self.writeVcdHeaderStart()
        self.writeComponentHeader(ddic['top'])
        self.writeVcdHeaderEnd()
        self.writeVcdInitValuesStart()
         
        self.writeVcdInitValuesEnd()
         
        with open(self.vcd_out_path + "/" + self.vcd_filename + ".tmp", 'r+') as vcdfile_tmp:
            for line in vcdfile_tmp:
                if line[0] == '#':
                    self.vcdfile.write(line)
                else:
                    code = line.split(' ')[1].strip()
                    if code in self.used_codes:
                        self.vcdfile.write(line)
         
        self.vcdfile.close()
     
    def writeVcdHeaderStart(self):
        self.vcdfile.write("$date\n")
        self.vcdfile.write("    {0}\n".format(time.asctime()))
        self.vcdfile.write("$end\n")
        self.vcdfile.write("$version\n")
        self.vcdfile.write("    FPyGA {0}\n".format(__version__))
        self.vcdfile.write("$end\n")
        self.vcdfile.write("$timescale\n")
        self.vcdfile.write("    {0}\n".format(self.timescale))
        self.vcdfile.write("$end\n")
        self.vcdfile.write("\n")
         
    def writeVcdHeaderEnd(self):
        self.vcdfile.write("\n")
        self.vcdfile.write("$enddefinitions $end\n")
         
    def writeVcdInitValuesStart(self):
        self.vcdfile.write("$dumpvars\n")
         
    def writeVcdInitValuesEnd(self):
        self.vcdfile.write("$end\n")
     
    
    def component_hier_dfs(self, hier, path):
        self.writeComponentHeaderStart(ddic[path])
        for name, c in hier.items():
            if isinstance(c, VCDTrace):
                c.print_var_declaration()
                self.used_codes.add(c.code)
            else:
                self.component_hier_dfs(c, '/'.join([path, name]))
                
        self.writeComponentHeaderEnd()
    
    def writeComponentHeader(self, top):
#         self.visited_traces = set()
#         component_visitor(top, before_comp=self.writeComponentHeaderVisitorBegin, end_comp=self.writeComponentHeaderVisitorEnd)
        hier = {}
        
        for trace in self.trace_list:
            name = trace.isig.name
            trace.vcdfile = self.vcdfile
            path = name.split('/')
            hier_cur = hier
            for p in path[1:-1]:
                if p not in hier_cur:
                    hier_cur[p] = {}
                    
                hier_cur = hier_cur[p]
                
            hier_cur[path[-1]] = trace
            
        self.component_hier_dfs(hier, 'top')
            
#         for c, name in top.c.items():
#             if c.c:
#                 self.writeComponentHeaderStart(c)
#          
#             if hasattr(c, "traces"):
#                 if id(c.traces) not in self.visited_traces:
#                     self.visited_traces.add(id(c.traces))
#                     if isinstance(c.traces, (tuple, list)):
#                         for t in c.traces:
#                             t.print_var_declaration()
#                             self.used_codes.add(t._code)
#                     else:
#                         if c.traces is not None:
#                             c.traces.print_var_declaration()
#                             self.used_codes.add(c.traces._code)
         
    def writeComponentHeaderStart(self, c):
        self.vcdfile.write("$scope module {0} $end\n".format(c.name))
     
    def writeComponentHeaderEnd(self):
        self.vcdfile.write("$upscope $end\n")
         
    def write_timestamp(self, time, sim):
        self.vcdfile.write("#{0}\n".format(time))
        return True
#         
#     def add_trace(self, trace):
#         self.trace_list.append(trace)
#         
#         code =  "".join(self.last_code)
#     
#         if self.last_code[2] != 'z':
#             self.last_code[2] = chr(ord(self.last_code[2]) + 1)
#         else:
#             if self.last_code[1] != 'z':
#                 self.last_code[1] = chr(ord(self.last_code[1]) + 1)
#                 self.last_code[2] = 'a'
#             else:
#                 self.last_code[0] = chr(ord(self.last_code[0]) + 1)
#                 self.last_code[1] = 'a'
#                 self.last_code[2] = 'a'
#             
#         return code
#     
    def printVcdStr(self, c_prop):
        self.tf.write("s{0} {1}".format(str(self.isig.read()), self._code))
         
    def printVcdHex(self):
        self.tf.write("s{0} {1}".format(hex(self.isig.read()), self._code))
 
    def printVcdBit(self, tf):
        self.tf.write("{0}{1}".format(self.isig.read(), self._code))
 
    def printVcdVec(self, tf):
        self.tf.write("b{0} {1}".format(bin(self.isig.read(), self._nrbits), self._code))
#     
#     def write_traces(self, time, sim):
#         for t in self.trace_list:
#             if t.changed():
#                 t.print_val()
#                 
#         return True
#     
#     def write_delta_traces(self, time, delta_count, sim):
#         if delta_count:
#             self.write_timestamp(time + delta_count/self.max_delta_count, sim)
#                                 
#             for t in self.trace_list:
#                 if t.changed():
#                     t.print_val()
#                 
#         return True            
# 
    def flush(self, sim):
        self.vcdfile.close()
        return True
     
#     def writeComponentHeaderVisitorBegin(self, c, tracer=None):
#          
#         if (c.components) or (self.channel_hrchy and hasattr(c, "traces")):
#             self.writeComponentHeaderStart(c)
#          
#         if hasattr(c, "traces"):
#             if id(c.traces) not in self.visited_traces:
#                 self.visited_traces.add(id(c.traces))
#                 if isinstance(c.traces, (tuple, list)):
#                     for t in c.traces:
#                         t.print_var_declaration()
#                         self.used_codes.add(t._code)
#                 else:
#                     if c.traces is not None:
#                         c.traces.print_var_declaration()
#                         self.used_codes.add(c.traces._code)
#          
#     def writeComponentHeaderVisitorEnd(self, c, tracer=None):
#         if (c.components) or (self.channel_hrchy and hasattr(c, "traces")):
#             self.writeComponentHeaderEnd()   
#     
#     def __init__(self, sim_events):
#         self.configurator = RequiredVariable('Configurator')
#         self.vcd_filename = self.configurator['VCDTracer', 'filename', 'sydpy.vcd']
#         self.channel_hrchy = self.configurator['VCDTracer', 'channel_hrchy', True]
#         self.vcd_out_path = self.configurator['VCDTracer', 'path', self.configurator['sys', 'output_path', self.configurator['sys', 'project_path'] + "/out"]]
#         self.timescale = self.configurator['sys', 'timescale', '100ps']
#         self.trace_deltas = self.configurator['VCDTracer', 'trace_deltas', False]
#         self.max_delta_count = self.configurator['sys.sim', 'max_delta_count', 1000]
#         
#         if (not os.path.isdir(self.vcd_out_path)):
#             os.makedirs(self.vcd_out_path, exist_ok=True)
#         
#         self.vcdfile = open(self.vcd_out_path + "/" + self.vcd_filename + ".tmp", 'w')
#         
#         self.trace_list = []
#         self.last_code = ['a', 'a', 'a']
# #         sim_events['run_start'].append(self.writeVcdHeader)
#         sim_events['timestep_start'].append(self.write_timestamp)
#         sim_events['timestep_end'].append(self.write_traces)
#         
#         if self.trace_deltas:
#             sim_events['delta_start'].append(self.write_delta_traces)
#             
#         sim_events['run_end'].append(self.writeVcdHeader)
# #         sim_events['run_end'].append(self.flush)
#         
#         features.Provide('VCDTracer', self)
#   
class VCDTrace():
    def __init__(self, isig, vcdfile, code):
        self.isig = isig
        self.vcdfile = vcdfile
        self.code = code
    
#     def print_init_val(self):
#         self.isig.read() = self._init
#         if self.isig.read() is not None:
#             self._print_val()
         
    def print_val(self):
        if isinstance(self.isig.read(), bool):
            self.vcdfile.write("b{0} {1}\n".format(int(self.isig.read()), self.code))
        elif hasattr(self.isig.read(), 'bitstr'):
            self.vcdfile.write("b{0} {1}\n".format(self.isig.read().bitstr(), self.code))
        else: # default to 'string'
            self.vcdfile.write("s{0} {1}\n".format(str(self.isig.read()).replace(' ', '').replace("'", ""), self.code))
     
    def print_var_declaration(self):
        name = self.isig.name.replace(':','_').replace('[', '_').replace(']', '')
        if isinstance(self.isig.read(), bool):
            s = "$var wire 1 {0} {1} $end\n".format(self.code, name)
        elif hasattr(self.isig.read(), 'bitstr'):
            str_val = self.isig.read().bitstr()
             
            if len(str_val) == 3:
                s = "$var wire 1 {0} {1} $end\n".format(self.code, name)
            else:
                s = "$var wire {0} {1} {2} $end\n".format(len(str_val) - 2, self.code, name)
        else: # default to 'string'
            s ="$var real 1 {0} {1} $end\n".format(self.code, name)
         
        self.vcdfile.write(s)
 

 
# class VCDTraceMirror(VCDTrace):
#     
#     def _find_src_trace(self):
#         for t in self._src.traces:
#             if t._name == self._src_trace_name:
#                 return t
#         
#     def print_var_declaration(self):
#         src_trace = self._producer._get_base_trace()
#         self._code = src_trace._code
#         self.isig.read() = src_trace._val
#         
#         VCDTrace.print_var_declaration(self)
#     
#     def __init__(self, name, producer):
#         self._name = name
#         self._producer = producer
#         self._tracer = RequiredVariable('VCDTracer')

