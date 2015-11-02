from sydpy import *
import os

class Stimulus(Component):
    @compinit
    def __init__(self, ch_logic_clk_i, ch_data_clk_i, ch_system_reset_i,
             ch_scr_i, ch_cs_i, ch_da_i, ch_data_i, 
             ch_data_o, ch_intrq_o, ch_dior_i, ch_diow_i, ch_diordy_o,
             logic_clk_period=10, data_clk_period=20, **kwargs):

        ch_logic_clk_i <<= self.inst("logic_clk_i", isig, dtype=bit, dflt=0)
        ch_data_clk_i <<= self.inst("data_clk_i", isig, dtype=bit, dflt=0)
        ch_system_reset_i <<= self.inst("system_reset_i", isig, dtype=bit, dflt=1)
        ch_scr_i <<= self.inst("scr_i", isig, dtype=bit)
        ch_cs_i <<= self.inst("cs_i", isig, dtype=Bit(2))
        ch_da_i <<= self.inst("da_i", isig, dtype=Bit(3))
        ch_data_i <<= self.inst("data_i", isig, dtype=bit32, dflt=0)
        ch_data_o >>= self.inst("data_o", isig, dtype=bit32)
        ch_intrq_o >>= self.inst("intrq_o", isig, dtype=bit)
        ch_dior_i <<= self.inst("dior_i", isig, dtype=bit)
        ch_diow_i <<= self.inst("diow_i", isig, dtype=bit)
        ch_diordy_o >>= self.inst("diordy_o", isig, dtype=bit)
        
        self.inst("p_logic_clk", Process, self.p_logic_clk, [Delay(logic_clk_period // 2)])
        self.inst("p_data_clk", Process, self.p_data_clk, [Delay(data_clk_period // 2)])
        self.inst("p_stim", Process, self.p_stim, [self.data_clk_i.e.posedge])
        self.inst("p_reset", Process, self.p_reset, [])
        
        self.state = "init"
        
    def p_stim(self):
        self.cs_i <<= 1
        self.da_i <<= 0
        self.scr_i <<= 0
        self.diow_i <<= 0
        self.dior_i <<= 0        
        
        if self.state == "init":
            if self.diordy_o and (not self.system_reset_i):
                self.state = "write"
        elif self.state == "write":
            self.diow_i <<= 1
            self.data_i <<= self.data_i + 1
            self.state = "read_wait"
        elif self.state == "read_wait":
            self.state = "read"
        elif self.state == "read":
            self.dior_i <<= 1
            self.state = "write_wait"
        elif self.state == "write_wait":
            self.state = "write"
    
    def p_reset(self):
        system.sim.wait([Delay(4*self.data_clk_period)])
        self.system_reset_i <<= '0'
    
    def p_logic_clk(self):
        self.logic_clk_i <<= ~self.logic_clk_i

    def p_data_clk(self):
        self.data_clk_i <<= ~self.data_clk_i

class Sata(Cosim):
    @compinit
    def __init__(self, ch_logic_clk_i, ch_data_clk_i, ch_system_reset_i,
                 ch_scr_i, ch_cs_i, ch_da_i, ch_data_i, 
                 ch_data_o, ch_intrq_o, ch_dior_i, ch_diow_i, ch_diordy_o,  **kwargs):

        ch_logic_clk_i >>= self.inst("logic_clk_i", isig, dtype=bit)
        ch_data_clk_i >>= self.inst("data_clk_i", isig, dtype=bit)
        ch_system_reset_i >>= self.inst("system_reset_i", isig, dtype=bit)
        ch_scr_i >>= self.inst("scr_i", isig, dtype=bit)
        ch_cs_i >>= self.inst("cs_i", isig, dtype=Bit(2))
        ch_da_i >>= self.inst("da_i", isig, dtype=Bit(3))
        ch_data_i >>= self.inst("data_i", isig, dtype=bit32)
        ch_data_o <<= self.inst("data_o", isig, dtype=bit32)
        ch_intrq_o <<= self.inst("intrq_o", isig, dtype=bit)
        ch_dior_i >>= self.inst("dior_i", isig, dtype=bit)
        ch_diow_i >>= self.inst("diow_i", isig, dtype=bit)
        ch_diordy_o <<= self.inst("diordy_o", isig, dtype=bit)

class TestSata(Component):
    @compinit
    def __init__ (self, name):
        for ch in ['ch_logic_clk_i', 'ch_data_clk_i', 'ch_system_reset_i',
             'ch_scr_i', 'ch_cs_i', 'ch_da_i', 'ch_data_i', 
             'ch_data_o', 'ch_intrq_o', 'ch_dior_i', 'ch_diow_i', 'ch_diordy_o']:
            self.inst(ch, Channel)
            
        self.inst('sata', Sata, ch_logic_clk_i=self.ch_logic_clk_i, ch_data_clk_i=self.ch_data_clk_i, ch_system_reset_i=self.ch_system_reset_i,
             ch_scr_i=self.ch_scr_i, ch_cs_i=self.ch_cs_i, ch_da_i=self.ch_da_i, ch_data_i=self.ch_data_i, 
             ch_data_o=self.ch_data_o, ch_intrq_o=self.ch_intrq_o, ch_dior_i=self.ch_dior_i, ch_diow_i=self.ch_diow_i, ch_diordy_o=self.ch_diordy_o,
             module_name='so_ip_sata_host_tb')
        self.inst('stim', Stimulus, ch_logic_clk_i=self.ch_logic_clk_i, ch_data_clk_i=self.ch_data_clk_i, ch_system_reset_i=self.ch_system_reset_i,
             ch_scr_i=self.ch_scr_i, ch_cs_i=self.ch_cs_i, ch_da_i=self.ch_da_i, ch_data_i=self.ch_data_i, 
             ch_data_o=self.ch_data_o, ch_intrq_o=self.ch_intrq_o, ch_dior_i=self.ch_dior_i, ch_diow_i=self.ch_diow_i, ch_diordy_o=self.ch_diordy_o)


conf = [
        ('sim'              , Simulator),
        ('xsim'             , XsimIntf),
        ('server'           , Server),
#         ('profiler'         , Profiler),
        ('xsim.builddir'    , './xsim'),
        ('top.*.cosim_intf', 'xsim'),
        ('top.sata.fileset', ['/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_ip_sata_pkg.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_scrambler_rtl.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_ip_crc32_rtl.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_sata_crc32_soft_ip.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_two_byte_fifo_rtl.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_speed_neg_control_rtl.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_phy_init_fsm_rtl.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_phy_layer_rtl.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_transport_layer_fsm_rtl.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_transport_layer_rtl.vhd', 
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_link_layer_fsm_rtl.vhd',                               
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_link_layer_rtl.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core/so_sata_cntrl_logic_rtl.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/tb/verification_environment/std_logic_textio.vhd',                              
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/tb/verification_environment/so_ip_sata_host_verification_environment_pkg.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/tb/verification_environment/so_ip_sata_device.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/tb/verification_environment/so_ip_phy_link.vhd',
                              '/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/tb/so_sata_cntrl_logic_cosim.vhd']
#                               [ os.path.join('/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core',f) for f in os.listdir('/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core') if os.path.isfile(os.path.join('/home/bvukobratovic/projects/sata/svn/trunk/src/vhdl/core',f))]
                            ),
        ('top'          , TestSata),
        ('sim.duration'     , 2000)
        ]

system.set_config(conf)
system.sim.run()
