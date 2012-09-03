.. Website meta-data:
.. TITLE:User's Guide
.. MENU_ITEM:Documentation

User's Guide
============

This guide is a very rough and ready guide to getting this program running
followed by notes about using various UI features.

Requirements
------------

The following software/libraries are needed.

* Python 2.6 (Not tested with Python 3-series)
* PyGTK (Tested under version 2.17, may work on older versions)
* PySerial
* Python ELFtools (Optional: for ELF-file support)

Getting Started
---------------

You can start Perentie with an emulator using::

	python /path/to/perentie/dir -e emulator_path [emulator args]

You can also start it connected to a serial device (such as the Manchester lab
boards set in a Komodo-compatible mode) using::

	python /path/to/perentie/dir -s /serial/port/path [-b baudrate]

If a serial port name of "0" is supplied, the system's default serial port is
used. The baudrate defaults to 115200.

If no arguments are given, the Target Selection window will be displayed which
allows you to interactively select a target. This window is also displayed if
the target defined in the arguments is not reachable.

Assuming the board is recognised and properly connected, the Main Window will be
displayed. This window contains a menubar and toolbar with various buttons for
controlling the board and assembling and loading programs. If registers are
available in the architecture, they are displayed on the left. On the right a
pair of memory viewers are provided if the architecture defines a memory.
Initially, the top memory viewer shows the memory in a source-code & disassembly
(if available) view and the bottom viewer initially shows CPU-words. Along the
bottom of the window, a status bar shows the attached device's state and above
it, the 'Error Log' expander can be clicked to toggle the display of error
messages. Important error messages will automatically expand the bar.

Values are, by default, shown in hexadecimal without a leading '0x'. You can
choose another base or enable or the display prefixes as required from the
Window menu.

Loading Programs
----------------

Clicking the assemble button will re-assemble the last program assembled or, if
nothing has been assembled yet, a file-browser is presented to select a file to
assemble. If the assembler fails, the error log will be displayed showing any
errors which occurred.

Clicking the load button behaves similarly for memory images. After running the
assembler, the memory image generated will be automatically selected and so
clicking Load immediately after assembling a program will load the assembled
program into memory.

To select a different file to assemble or load, click the drop-down arrow next
to the assemble and load buttons and click 'select source file' or 'select image
file' as appropriate.

Generally when re-loading a program you'll want to reset the device, assemble
the program and then load and run it. These actions are conveniently placed in
order on the toolbar and are assigned to F2-F5 respectively.

Controlling Execution
---------------------

The Reset, Run and Stop buttons should be fairly self explanatory.

Step will cause the processor to execute one instruction and then stop.

Multi-Step will cause the processor to execute the number of steps given in the
spin-box on the menu bar and then stop. Pressing 'Enter' in the (decimal) spin
box will also cause the multi-step action to be triggered. The Pause button
allows you to pause and resume multi-stepping.

Editing Registers
-----------------

Integer-containing registers can be edited by double clicking their value in the
list and entering an expression for the new value required (see 'Entering
Expressions'). Press Enter to confirm or escape to cancel.

Bit-fields (such as flag registers) can be edited using the bit-field editor at
the bottom of the register list. Individual bits can be toggled by clicking the
toggle buttons. Integer-sub-fields can be edited by entering an expression into
the entry box and pressing enter. Enumerated fields appear as drop-down menus of
options.  Hovering your mouse over a field (or the bit-field's name) will show
you the raw bit values of the relevant bits.

You can open additional register-viewer windows using 'New Register Viewer' in the
'Window' menu or by pressing Ctrl+R.

Editing Memory
--------------

You can jump to an address in memory by writing an expression in the 'Address'
box at the top left of a memory editor. If the 'Follow' option is selected the
window will scroll as the value of your expression changes. For example you
could use the expression "PC - 4" to keep the memory editor displaying the area
of memory pointed to by the program counter.

You can change the view shown in the memory viewer using the drop-down box at
the top right. The 'Align' option will forces the first address displayed to be
appropriately aligned for the current view. As well as straight-forward memory
and disassembly views, there are also hybrid source code/disassembler views.
These show the program source associated with each address or the disassembly if
the value has changed or wasn't defined in the image file.

Double clicking a field in the memory viewer allows a new value to be entered.
Some fields (for example the source field) cannot be edited. Fields which
contain numerical data support the entry of expressions. For example if viewing
an ARM memory with the one-word wide view, you can use the expression "mem[0:4]
* 2" to set the value to be the same as the first word of memory.

You can open additional memory-viewer windows using 'New Memory Viewer' in the
'Window' menu or by pressing Ctrl+M.

Entering Expressions
--------------------

Expressions can contain numbers, registers and memory values. You can then use
Python (C-style) arithmetic operators on these values. If the display of
prefixes is disabled in the Window menu, values given without a prefix will be
interpreted in that base. To force another base, simply use the appropriate
prefix. If prefixes are enabled, numbers are interpreted as decimal unless they
are prefixed appropriately. Unfortunately, integers cannot be entered in decimal
while prefixes are hidden (as no prefix exists for decimal values). Python has
unlimited-size integers and so there is no limit (short of system memory) to the
size of the integers supported.

For example, while in hexadecimal mode when prefixes are disabled, the following
expressions are valid::

	124A4fDC                              # A simple hex constant
	((124A4fDC * 3) & FF000000) >> 0b0110 # Multiplication, AND, shift, binary
	2 ** R2                               # Two to the power of R2

In any mode when prefixes are enabled::
	
	1234 + 5               # Simple decimal expression
	0xDEADBEEF + 0o4 + 0b1 # Hex, octal, binary

You can access registers from the register banks other than the first bank using
variables named register_bank_name.register_name. Registers in the first
register bank can be referred to simply by name. Some registers may also have
aliases (for example, in the STUMP, the PC is also named R7). To see a complete
list of these names a register has, hover over the register's name in the
register list. For example::

	PC
	R2 >> (R4 - 1)

Memory words can be accessed using memory_name[address]. You can access multiple
words using memory_name[start:end] (where end is not included) and the words
will be concatenated together but will not be sign extended. Memory names can be
found in the 'Device Info' window available in the 'Device' menu. For example::

	mem[0]
	mem[10:14] + 42
	mem[pc:pc+4]
	mem[mem[r3]]

The result of an expression will be masked off to fit the register or memory it
assigned to. If a signed value is produced, it will be sign-extended to the
correct width. If the result of an expression is a string of bytes/chars, it
will be converted into an integer using the b2i function (see below) before
being masked off to fit the memory.

Various utility functions are also provided. Most functions from the python 'math'
library are available, for example sin, cos, tan, ceil and floor. In addition
the following functions are also available:

min, max
	Return the minimum or maximum argument.
log2
	Log base 2
sign_extend(value, bits)
	Sign extend the given value to 'bits' bits wide.
abs
	Absolute value (make positive)
int
	Truncate a floating-point value (e.g. from sin) to an integer.
float
	Convert an integer to a floating point value (e.g. to allow floating point
	deivision)
ord
	Convert a char to its ASCII code.
chr
	Convert an ASCII code to a char.
sum
	Sum up all arguments, e.g. sum(r1, r2, r3)
map, reduce
	Google these for usage.
i2b(value, width_bits)
	Return a string of bytes/chars from the given value
b2i(value)
	Convert a string of bytes into an integer.

Misc Features
-------------

The values displayed by the GUI are refreshed periodically by default. This can
cause some overhead for the connected device which may reduce its performance.
Auto refresh be disabled by deselecting the 'Auto Refresh' option in the
'Device' menu. When auto refresh is disabled, the GUI can be refreshed using
'Refresh Now' in the device menu or by pressing the F1 key.

Details about the connected device can be found in the 'Device Info'
window in the 'Device' menu. This window lists all names for registers and
memories that can be used in expressions as well as many other system details.
