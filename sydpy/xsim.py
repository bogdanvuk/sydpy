from sydpy.component import Component, compinit, RequiredFeature
import string
import os
import itertools
from subprocess import Popen, PIPE

wrapper_tmpl = string.Template("""
module wrap();

    import "DPI-C" pure function void xsimintf_init ();
    import "DPI-C" pure function void xsimintf_export (input string s);
    import "DPI-C" pure function string xsimintf_import ();
    import "DPI-C" pure function int xsimintf_wait ();
    
    ${port_definition}
    
    initial
    begin
        xsimintf_init();
    end
    
    always #1 begin
        automatic integer vals_read;
        automatic string   strimp;
        automatic integer  delay;
        
        delay = xsimintf_wait();
        #delay;
        strimp = xsimintf_import();
        vals_read = $$sscanf(strimp, ${import_str_format}, ${in_port_list});
    end

    always_comb begin
        automatic string       strexp;
        automatic string       strimp;
        automatic integer vals_read;
        
        $$sformat(strexp, ${export_str_format}, ${out_port_list});
        xsimintf_export(strexp);
        strimp = xsimintf_import();
        vals_read = $$sscanf(strimp, ${import_str_format}, ${in_port_list});
    end
    
    ${module_instantiation}

endmodule   
""")

module_inst_tmpl = string.Template("""
  ${module_name} ${instance_name} (
    ${port_map}
  );
""")

port_map_tmpl = string.Template(".${port_name} (${signal_name})")

def shell(cmd):
    print(' '.join(cmd))
    p = Popen(' '.join(cmd), shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    out, err = p.communicate()
    print("Return code: ", p.returncode)
    print(out.rstrip(), err.rstrip())

class XsimIntf(Component):

    sim = RequiredFeature('sim')
    server = RequiredFeature('server')

    @compinit
    def __init__(self, builddir='.', **kwargs):
        self.cosim_pool = []
        self.sim.events['run_start'].append(self.sim_run_start)
        self.sim.events['run_end'].append(self.sim_run_end)
        self.sim.events['delta_settled'].append(self.sim_delta_settled)
        self.sim.events['timestep_start'].append(self.sim_timestep_start)
        
    
    def render_module_inst(self, cosim):
        port_map = []
        for name, intf in itertools.chain(cosim.inputs.items(), cosim.outputs.items()):
            port_map.append(port_map_tmpl.substitute(port_name = name, signal_name = '_'.join([cosim.module_name, name]))) 
    
        return module_inst_tmpl.substitute(module_name=cosim.module_name,
                                           instance_name='i_' + cosim.module_name,
                                           port_map=',\n    '.join(port_map))
    
    def render_wrapper(self):
        module_insts = []
        for cosim in self.cosim_pool:
            module_insts.append(self.render_module_inst(cosim))
        
        ports_definition = []
        for name, intf in sorted(itertools.chain(self.inputs.items(), self.outputs.items())):
            if intf.dtype.w == 1:
                ports_definition.append('logic {0};'.format(name))
            else:
                ports_definition.append('logic [{0}:0] {1};'.format(intf.dtype.w-1,name))
        
        import_str_format  = ['%d']*len(self.inputs)
        export_str_format  = ['%d']*len(self.outputs)

        return wrapper_tmpl.substitute(
                                       port_definition='\n  '.join(ports_definition),
                                       import_str_format='"{0}"'.format(' '.join(import_str_format)),
                                       in_port_list = ','.join(sorted(self.inputs.keys())),
                                       export_str_format='"{0}"'.format(' '.join(export_str_format)),
                                       out_port_list = ','.join(sorted(self.outputs.keys())),
                                       module_instantiation = '\n\n'.join(module_insts)
                                       )

    def resolve_cosims(self):
        self.inputs = {}
        self.outputs = {}
        self.fileset = []
        for cosim in self.cosim_pool:
            cosim.resolve()
            self.inputs.update({'_'.join([cosim.module_name, k]):v for k,v in cosim.inputs.items()})
            self.outputs.update({'_'.join([cosim.module_name, k]):v for k,v in cosim.outputs.items()})
            self.fileset.extend(cosim.fileset)
    
    def sim_run_start(self, sim):
        self.cosim_time = 0
        self.resolve_cosims()
        os.makedirs(self.builddir, exist_ok=True)
        os.chdir(self.builddir)
        
#         print(self.render_wrapper())
        text = self.render_wrapper()
#         with open(os.path.join(self.builddir, "wrapper.sv"), "w") as text_file:
        with open("wrapper.sv", "w") as text_file:
            text_file.write(text)

#         self.fileset.append(os.path.join(self.builddir, "wrapper.sv"))
        self.fileset.append('wrapper.sv')

        shell(cmd = ['xvlog', '-sv'] + self.fileset)
        shell(cmd = ['xelab', '-m64', '-svlog', 'wrapper.sv', '-sv_root', '/home/bvukobratovic/projects/sydpy/intf/xsim/xsim.dir/xsc', '-sv_lib', 'dpi', '-debug', 'all'])
#         shell(cmd = ['xsim', 'work.wrap', '-t', '/home/bvukobratovic/projects/sydpy/tests/dpi/run.tcl'])
        cmd = ['xsim', 'work.wrap', '-t', '/home/bvukobratovic/projects/sydpy/tests/dpi/run.tcl']
        self.xsim_proc = Popen(' '.join(cmd), shell=True, stdout=PIPE, stderr=PIPE, universal_newlines=True)
    
    def sim_run_end(self, sim):
        self.xsim_proc.terminate()
    
    def sim_timestep_start(self, time, sim):
        self.cosim_time = time
    
    def sim_delta_settled(self, sim):
        if self.update:
            pass
        
    def updated(self, cosim):
        self.update = True
    
    def register(self, cosim):
        self.cosim_pool.append(cosim)
        
    def __del__(self):
        try:
            self.xsim_proc.terminate()
        except:
            pass

def generate_wrapper(modules):
    for name, port_list in modules:
        pass

def extract_port_struct(port_list): 
    ports = {}
    for port in port_list:
        cur_level = ports
        path = port.split('.')
        
        for i, p in enumerate(path):
            if '[' in p:
                name, index = p.split('[')
                index = index.split(']')[0]
            else:
                name = p
                index = None
                
            if name not in cur_level:
                if i < len(path) - 1:
                    cur_level[name] = {}
                else:
                    cur_level[name] = 0
            
            if i < len(path) - 1:
                if index is not None:
                    cur_level = cur_level[name][index]    
                else:
                    cur_level = cur_level[name]
            else:
                cur_level[name] += 1
    
    return ports

ports_str = r'clk int2\\.ready int2\\.request int2\\.value[0] int2\\.value[1] int2\\.value[2] int2\\.value[3] rst'        
extract_port_struct(ports_str.replace(r'\\', '').split(' '))