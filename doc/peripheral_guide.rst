Peripheral Guide
================

This guide describes the usage of various peripherals which are available on
certain devices. All supported peripherals are displayed as a tool-bar icon and
are listed in the 'Peripherals' menu. If no supported peripherals are found, the
menu is not shown.


Xilinx FPGA Loader
------------------

To upload a design, select the bit file using the file-selector button and click
'Send to FPGA'. The details of the bit-file will be shown alongside the current
contents of the FPGA (if known). The 'Refresh' button will update the file
meta-data.

The 'Erase FPGA' button will reset the FPGA removing the design it contained.

Errors will be reported in the error log in the Main Window.


Debug Controller
----------------

This peripheral is used by the 'ARM Host Program' which is a program which runs
on the Manchester Lab Board and allows the development of simple 16-bit CPUs on
the FPGA. This peripheral is provided to allow fine-grained controllability and
observability for the attached device.

The number of clock-cycles executed before the device's fetch signal is asserted
is displayed (i.e. how long the current instruction has taken to execute). You
can also manually send a clock-pulse (High followed by Low) to the device using
the 'Clock' button.  Manually clocking the device will automatically pause
execution.

The state of the memory interface is displayed underneath. Note that when the
memory interface's write-enable signal is asserted, it takes priority so you
will not be able to override this value in memory.

If the scan-path used to retrieve registers from the device is being extended
with user-defined registers, you can load a description of the scan path using
the scan-path tab. The description should be a series of register-sizes each on
its own line. Once loaded, the additional registers are displayed in the
'Signals' register bank as User0, User1, and so on. Note that although these
registers are shown as 16-bits wide in the GUI, the underlying registers are the
correct width and any excess bits will be ignored. Loading the scan-path
description also triggers a reset.
