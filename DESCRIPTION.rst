================
Welcome to SyDPy
================

SyDPy (**System Design in Python**) aims to become an alternative to SystemVerilog and 
`SystemC <http://www.accellera.org/downloads/standards/systemc>`_ by providing the necessary tools to cover tasks of 
HDL design from system architecture design to HDL synthesis.

SyDPy comprises an event based simulator and various classes for describing and simulating a system, all written in Python. 
This allows an easy extension of the SyDPy with additional user classes or existing Python libraries

SyDPy was written with design reuse and iterable nature of the design process in mind. Smart channels enable cosimulation of 
module architectures written on various abstraction levels (of timing and functionality), without the need of explicit 
interface converters in the design. Modules with higher levels of abstraction can then serve as model checkers for lower
level modules. 

SyDPy features:
===============
 - RTL and TLM cosimulation
 - Smart channels for information exchange between various interfaces
 - Global simulator configuration for test setup
 - Basic randomization, sequencing and scoreboarding supported
 - Automatic model checking between different module architectures
 - Extendible simulator kernel
 
Soon available:
===============
 - Verilog cosimulation using `Verilator <http://www.veripool.org/wiki/verilator>`_
 - Python to Verilog conversion
 - Constrained-random verification using `SystemC Verification <http://www.accellera.org/downloads/standards/systemc>`_ library
 
Getting started
===============

Installation
------------

Install SyDPy using pip::

  pip install sydpy

Install SyDPy using easy_install::

  easy_install sydpy
  
Install SyDPy from source::

  python setup.py install

Read the documentation
----------------------

Read the `SyDPy documentation <http://sydpy.readthedocs.org/en/latest/>`_

Checkout the examples
---------------------

Examples are located in the `examples <https://github.com/bogdanvuk/sydpy/tree/master/examples>`_ repository folder.

Get involved
------------

Pull your copy from `github repository <https://github.com/bogdanvuk/sydpy>`_


 