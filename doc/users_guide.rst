User's Guide
============

This guide is a very rough and ready guide to getting this program running
followed by notes about using various UI features.

Getting Started
---------------

You can start the debugger with an emulator using:

  python main.py -e [emulator path] [emulator args]

You can also start the debugger connected to a serial device (such as the
Manchester lab boards set in a Komodo-compatible mode) using

  python main.py -s [/serial/port/name] [-b baudrate]

By default a serial connection on the system's default serial port is assumed at
with a baudrate of 115200.

Assuming the board is recognised and properly connected, the GUI will be
displayed. The GUI contains a toolbar with various buttons for controlling the
board and assembling and loading programs. On the left there is a viewer for the
device's registers. On the right a pair of memory viewers are provided. They are
both equivalent but provided for convenience. Finally, at the bottom of the
window, the error log can be accessed by clicking the expander.

Loading Programs
----------------

Clicking the assemble button will re-assemble the last program assembled or, if
nothing has been assembled yet, a file-browser is presented to select a file to
assemble. If the assembler fails, the error log will be displayed showing any
errors which occurred.

Clicking the load button behaves similarly for memory images. After running the
assembler, the memory image generated will be automatically selected and so
clicking Load will load the assembled program into memory.

To select a different file to assemble or load, click the drop-down arrow next
to the assemble and load buttons and click 'select source file' or 'select image
file' as appropriate.

Controlling Execution
---------------------

The Reset, Run and Stop buttons should be fairly self explanatory.

Step will cause the processor to execute one instruction and then stop.

Multi-Step will cause the processor to execute the number of steps given in the
spin-box on the menu bar and then stop. The Pause button allows you to pause and
resume multi-stepping.

Editing Registers
-----------------

Integer-containing registers can be edited by double clicking their value in the
list and entering an expression for the new value required (see 'Entering
Expressions'). Press Enter to confirm or escape to cancel.

Bit-fields can be edited using the bit-field editor at the bottom of the
register list. Individual bits can be toggled by clicking the toggle button.
Integer-sub-fields can be edited by entering an expression into the entry box
and pressing enter. Enumerated fields appear as drop-down menus of options.
Hovering your mouse over a field (or the bit-field's name) will show you the
raw value of the relevant bits.

Editing Memory
--------------

You can jump to an address in memory by writing an expression in the 'Address'
box at the top left of a memory editor. If the 'Follow' option is selected the
window will scroll as the value of your expression changes.

You can change the view shown in the memory viewer using the drop-down box at
the top right. The 'Align' option will forces the first address displayed to be
appropriately aligned for the current view.

Double clicking a field in the memory viewer allows an expression to be entered
to specify the new value for for that part of memory.

Entering Expressions
--------------------

Expressions can contain numbers as either decimal, hex (prefixed with 0x) and
binary (prefixed with 0b) numbers. Variables corresponding to registers and
memories are also provided.

Python/C-style arithmetic is supported.

You can access registers from the register banks other than the first bank using
variables named register_bank_name.register_name.

Memory addresses can be accessed using memory_name[address].

The result of an expression will be masked off to fit the register or memory it
assigned to.
