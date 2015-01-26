..  _tutorial:

SyDPy short tutorial
====================

SyDPy 

Designing the D Flip Flop (DFF) with sig interface only:
--------------------------------------------------------

from sydpy import *

class Dff(Module):
    @arch_def
    def rtl(self, 

            clk: sig(bit), 
            din: sig(bit), 
            dout: sig(bit).master
            ):
        
        @always(self, clk.e.posedge)
        def reg():
            dout.next = din

Verification environment for DFF
--------------------------------

In order to simulate the design, we need to supply some stimulus and examine the output. The testbench module might look like this:
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    from sydpy import Module, architecture, clkinst
    from dff import DFF
    
    class TestDFF(Module):
    @architecture
    @clkinst('.clk', 100)
    def test1(self):
        self.sequencer(defseq = 'basic_rnd_seq', seq_o = '.din', aspect=bit)
        self.inst(DFF, clk='.clk', din='.din', dout='.dout')
        
We achieved the following with our testbench:
1.	We will have a steady clock with 100 tick period
2.	We will have a sequence of random bits fed into our DFF module

Simulating the design
---------------------

We need to form a configuration dictionary to properly setup the simulator. The minimum we have to supply is:
:::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    config = {
        'sys.duration' : 1000,
        'sys.top'      : TestDFF
    }

We can now run the simulation using::
    s = Simulator(config)
    
We won't see much what happened using this configuration. Easiest way to view the results is to activate the VCDTrace extension module. This can be accomplished by creating the 'sys.extensions' entry in the configuration dictionary and listing the VCDTrace::
    config = {
        'sys.extension' : ['VCDTrace'],
        'sys.duration'  : 1000,
        'sys.top'       : TestDFF
    }

If we run the simulation again, the VCD file will now be generated, and we can inspect the signals to verify the DFF design.

Channels, Proxies and Aspects
-----------------------------

Let's add the following member function to our DFF module::
	@architecture
	def seq(self, clk,
		din : seq(None, '.clk'),
		dout ):

        dout <<= din    
        
We declared a new architecture �seq� that performs identically to the previous one, but in fewer lines of code (OK, it's the same number of lines since I broke port list in three lines, but it's definitely less information supplied). The information that specified the FF process is now supplied in two places:
1.	din: seq(None, '.clk')
    In this way, using function annotation, we supplied the aspect (has the same purpose as the data type, but has a temporal dimension too) to the input port din. The seq (short for sequential) aspect forces the value of the variable din to be updated only at the rising edge of the clock (it does a bit more, but that's enough for now).
2.	dout <<= din
    This statement forces dout copies the value from din, whenever din value changes. It is the equivalent of Verilog assign statement.
    
In other words, output port dout will receive the value of the input din sampled at the rising edge of the clock � as any decent FF would do.
Since now we have two architectures for the DFF module, we need to specify which one should be used by the simulator (or it will pick one randomly). This can be done in two ways:
    1.	It can be supplied during module instantiation::
        self.inst(DFF, arch='seq', clk='.clk', din='.din', dout='.dout')
    2.	It can be supplied using configuration dictionary, with the following entry:
        'top.DFF.arch'	: 'seq'
	
In this way the arch setting of the DFF module is uniquely identified via hierarchical path.	
Note: The Test module received the name 'top', as all the top modules do. The DFF module got the name 'DFF' since we haven't supplied an other during instantiation.
The two ways basically do the same thing: set the 'arch' initialization argument of the DFF module to 'seq'. During the initialization, the member function with that name will be searched within the module dictionary and called.

If we run the simulation again, we should get the same VCD waveform.

Channels carry information
--------------------------
In order to simulate our design, SyDPy simulator created three different channels: 'clk', 'din' and 'dout'. The channels are used to carry the information between the processing units. The same information from a channel can be read in different ways, which are defined by the aspects of the variables. The variables in our design have the following aspects:
    1.	The sequencer
        1.1 seq_o � tlm(bit) , connected to the 'din' channel
            The 'tlm' (Transaction Level Model) part of the aspect is not supplied to the sequencer, but is implied since all sequencers output. This means that the sequencer will write to the 'din' channel in form of the 1 bit transactions. Please refer to chapter X for differences between tlm, sig and seq. (The basic_rnd_sequence module has automatic flow control, and will not send new transaction until the previous one has been consumed.)
    2.	DFF
        2.1	clk � sig(), connected to the 'clk' channel
            The 'sig' (short for signal) aspect is not explicitly supplied, but is implied whenever no aspect is given. When reading from channel with 'sig' aspect, one is always reading the current channel information (as opposed to 'seq' aspect, se below, and 'tlm aspect, see section X).
        2.2 din � seq(None, '.clk')
            When reading from channel with 'seq' aspect, one will read the information on the channel sampled at the rising edge of the supplied clock.
        2.3 dout � sig()

So what happens is that sequencer is generating 1 bit transactions and is writing them to the channel 'din'. The din variable in the DFF module, reads the transactions from the channel at the rising edge of the clock. Whenever the read value changes, the 'dout' channel is written with it.

Therefore in SyDPy we can have not only data type conversion, but also the temporal conversion, where information doesn't have to be read at the same moment and can also be split (see chapter X) and combined in time. In short, we have:
	one channel 	- 	one piece of information - 	multiple ways to read the information
	

