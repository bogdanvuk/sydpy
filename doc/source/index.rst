
Welcome to SyDPy
==================================

SyDPy project started in an attempt to customize the MyHDL Python package to my needs as FPGA designer. After realization that I have already done too much tweaking, I decided to write my own package from ground-up, but kept some of the MyHDL syntax for hardware description. The following are major differences to MyHDL:

- SyDPy enables TLM (Transaction Level Modelling)
- Signals are abstracted into channels. Information in the same channels can be accessed by different processes using different protocols (on various levels of abstraction) without the need of user conversion modules.
- Introduced global simulator configuration where user module parameters can be set using qualified names. Wildcards also supported.
- Modules can have multiple architectures
- Simulator kernel relies on greenlet threading system.
- Event system has been generalized. Custom events can be created and they seamlessly operate with kernel.
- Simulator kernel is extendible by registering callbacks to simulator events.
- Basic randomization, sequencing and scoreboarding supported.

.. toctree::
   :maxdepth: 2

   roadmap
