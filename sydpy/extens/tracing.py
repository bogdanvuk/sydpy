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

"""Module implements VCDTracer simulator extension."""

import time
import os
from sydpy._util._injector import RequiredVariable, features  # @UnresolvedImport
from sydpy import __version__ #, EnumItemType
from sydpy._component import component_visitor

class VCDTracer(object):
    
    def writeVcdHeader(self, sim):
        self.vcdfile.close()
        self.vcdfile = open(self.vcd_out_path + "/" + self.vcd_filename, 'w')
        
        self.used_codes = set()
        
        self.writeVcdHeaderStart()
        self.writeComponentHeader(sim.top_module)
        self.writeVcdHeaderEnd()
        self.writeVcdInitValuesStart()
        
#         for t in self.trace_list:
#             if t._code in self.used_codes:
#                 t.print_init_val()
        
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
    
    def writeComponentHeader(self, top):
        self.visited_traces = set()
        component_visitor(top, before_comp=self.writeComponentHeaderVisitorBegin, end_comp=self.writeComponentHeaderVisitorEnd)
        
    def writeComponentHeaderStart(self, c):
        self.vcdfile.write("$scope module {0} $end\n".format(c.name))
    
    def writeComponentHeaderEnd(self):
        self.vcdfile.write("$upscope $end\n")
        
    def write_timestamp(self, time, sim):
        self.vcdfile.write("#{0}\n".format(time))
        return True
        
    def add_trace(self, trace):
        self.trace_list.append(trace)
        
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
            
        return code
    
    def printVcdStr(self, c_prop):
        self.tf.write("s{0} {1}".format(str(self._val), self._code))
        
    def printVcdHex(self):
        self.tf.write("s{0} {1}".format(hex(self._val), self._code))

    def printVcdBit(self, tf):
        self.tf.write("{0}{1}".format(self._val, self._code))

    def printVcdVec(self, tf):
        self.tf.write("b{0} {1}".format(bin(self._val, self._nrbits), self._code))
    
    def write_traces(self, time, sim):
        for t in self.trace_list:
            if t.changed():
                t.print_val()
                
        return True
    
    def write_delta_traces(self, time, delta_count, sim):
        if delta_count:
            self.write_timestamp(time + delta_count/self.max_delta_count, sim)
                                
            for t in self.trace_list:
                if t.changed():
                    t.print_val()
                
        return True            

    def flush(self, sim):
        self.vcdfile.close()
        return True
    
    def writeComponentHeaderVisitorBegin(self, c, tracer=None):
        
        if (c.components) or (self.channel_hrchy and hasattr(c, "traces")):
            self.writeComponentHeaderStart(c)
        
        if hasattr(c, "traces"):
            if id(c.traces) not in self.visited_traces:
                self.visited_traces.add(id(c.traces))
                if isinstance(c.traces, (tuple, list)):
                    for t in c.traces:
                        t.print_var_declaration()
                        self.used_codes.add(t._code)
                else:
                    if c.traces is not None:
                        c.traces.print_var_declaration()
                        self.used_codes.add(c.traces._code)
        
    def writeComponentHeaderVisitorEnd(self, c, tracer=None):
        if (c.components) or (self.channel_hrchy and hasattr(c, "traces")):
            self.writeComponentHeaderEnd()   
    
    def __init__(self, sim_events):
        self.configurator = RequiredVariable('Configurator')
        self.vcd_filename = self.configurator['VCDTracer', 'filename', 'sydpy.vcd']
        self.channel_hrchy = self.configurator['VCDTracer', 'channel_hrchy', True]
        self.vcd_out_path = self.configurator['VCDTracer', 'path', self.configurator['sys', 'output_path', self.configurator['sys', 'project_path'] + "/out"]]
        self.timescale = self.configurator['sys', 'timescale', '100ps']
        self.trace_deltas = self.configurator['VCDTracer', 'trace_deltas', False]
        self.max_delta_count = self.configurator['sys.sim', 'max_delta_count', 1000]
        
        if (not os.path.isdir(self.vcd_out_path)):
            os.makedirs(self.vcd_out_path, exist_ok=True)
        
        self.vcdfile = open(self.vcd_out_path + "/" + self.vcd_filename + ".tmp", 'w')
        
        self.trace_list = []
        self.last_code = ['a', 'a', 'a']
#         sim_events['run_start'].append(self.writeVcdHeader)
        sim_events['timestep_start'].append(self.write_timestamp)
        sim_events['timestep_end'].append(self.write_traces)
        
        if self.trace_deltas:
            sim_events['delta_start'].append(self.write_delta_traces)
            
        sim_events['run_end'].append(self.writeVcdHeader)
#         sim_events['run_end'].append(self.flush)
        
        features.Provide('VCDTracer', self)
  
class VCDTrace():
    def changed(self):
#         return self._producer.trace_val_updated
        val = self._producer.trace_val(self._name)
        if self._val != val:
            return True
        else:
            return False
    
    def print_val(self):
        self._val = self._producer.trace_val(self._name)
        self._print_val()
        
    def print_init_val(self):
        self._val = self._init
        if self._val is not None:
            self._print_val()
        
    def _print_val(self):
        if isinstance(self._val, bool):
            self._tracer.vcdfile.write("b{0} {1}\n".format(int(self._val), self._code))
        elif hasattr(self._val, 'bitstr'):
            self._tracer.vcdfile.write("b{0} {1}\n".format(self._val.bitstr(), self._code))
        else: # default to 'string'
            self._tracer.vcdfile.write("s{0} {1}\n".format(str(self._val).replace(' ', '').replace("'", ""), self._code))
    
    def print_var_declaration(self):
        name = self._name = self._name.replace(':','_').replace('[', '_').replace(']', '')
        if isinstance(self._val, bool):
            s = "$var wire 1 {0} {1} $end\n".format(self._code, name)
        elif hasattr(self._val, 'bitstr'):
            str_val = self._val.bitstr()
            
            if len(str_val) == 3:
                s = "$var wire 1 {0} {1} $end\n".format(self._code, name)
            else:
                s = "$var wire {0} {1} {2} $end\n".format(len(str_val) - 2, self._code, name)
        else: # default to 'string'
            s ="$var real 1 {0} {1} $end\n".format(self._code, name)
        
        self._tracer.vcdfile.write(s)

    def __init__(self, name, producer, init=None):
        self._tracer = RequiredVariable('VCDTracer')
        self._name = name
        self._init = init
        self._code = self._tracer.add_trace(self)
        self._producer = producer
        self._val = None

class VCDTraceMirror(VCDTrace):
    
    def _find_src_trace(self):
        for t in self._src.traces:
            if t._name == self._src_trace_name:
                return t
        
    def print_var_declaration(self):
        src_trace = self._producer._get_base_trace()
        self._code = src_trace._code
        self._val = src_trace._val
        
        VCDTrace.print_var_declaration(self)
    
    def __init__(self, name, producer):
        self._name = name
        self._producer = producer
        self._tracer = RequiredVariable('VCDTracer')

