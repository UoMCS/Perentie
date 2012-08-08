Developer Guide
===============

This tool was originally designed to be a Komodo-like debugging tool for the
STUMP and MU0 CPUs for use in COMP22111 at the University of Manchester. It
should also hopefully be flexible enough that a larger range of (more
complicated) processors can also be controlled by the interface with a modest
amount of work.


Code Conventions
----------------

Warnings of workarounds or bodges are indicated by "XXX".

Comments noting features which are anticipated or things that need polishing off
are indicated with "TODO".

Methods and functions starting with "xxx" are implementations of workarounds
and should eventually be removed.

Tabs are used for indentation, spaces are used for alignment. Any tab-width
should yield equally readable, properly indented code (to the indentation width
of the user's choice).


Overview
--------

The system consists of the following major components:

 * Architecture Definition
 * Back-end
 * System Interface
 * GUI Logic/Glue

The architecture definition is a general description of the registers and memory
available in the system being debugged. In principle, you should be able to
define a new architecture definition and the program will adapt to interface
correctly with this type of CPU.

The back-end is a low-level interface to a device (emulated or real). This
interface uses currently uses the KMD comms protocol. This unfortunately has
some limitations but these could be overcome in a future revision of the
protocol specification.

The system interface combines an architecture and back-end connected to a device
with a high-level device interface and logging capabilities amongst other
features.

The GUI glues together a user-interface with a system interface to allow a user
to interactively debug a device.

These components are discussed in the following sections.


Architecture Definition
-----------------------

All code relating to the system architecture definitions is contained in the
architecture package (contained within the directory of the same name).

An architecture is assumed to consist of a series of banks of registers, a
series of memories and a set of peripherals (known in the KMD parlance as
features). Registers and memories can have arbitrary word sizes. Registers may
further be described in terms of a bit-field and memories have an associated
address width, total size and disassembler.

Processor architectures are defined as a python class inheriting from the base
class Architecture in base.py. This class has various properties which must be
set according to the processor in question. See architecture/base.py for an
overview of the fields.

A few architectures have already been defined, the most complete (though not
most feature hungry) is probably the STUMP. This defines the STUMP CPU with its
single register bank, simple flag register and 16-bit memory. Take a look for
some reasonably well documented architecture descriptions. Further documentation
on the use of the various classes can be found within the doc-strings of the
classes in the architecture package.

The most complex definitions needed are likely to be for the assemblers and
disassemblers used by the architecture. See architecture/(dis)assembler/base.py
for a description of the interface an assembler or disassembler should provide.

Devices identify their architecture by a unique integer. Depending on the value
given, different architectures will be selected. The mapping from number to
architecture is specified in the get_architecture function in
architecture/__init__.py. New architectures should be listed here.

Notes
`````
Various parts of the architecture definition require a list of names. These
names must generally be valid Python identifiers as they will be made accessible
to the user in input expressions (which use the Python evaluator). The first of
these names will generally be used as the default when displaying the name in
the UI.



Back-End
--------

The back-end is a low-level interface to the device being debugged. Currently,
the back end is based on the KMD comms protocol. Code relating to the back-end
is contained in the back_end package (in the directory of the same name).

Two back-ends are provided which should prove adequate for most purposes.
EmulatorBackEnd (emulator.py) is a back-end which starts an external emulator
program in a subprocess (for example, Jimulator) and communicates via its
standard input/output pipes. The other back-end is the SerialPortBackEnd
(serial_port.py) which communicates with a device via a serial port.

Back-ends should inherit the base.BackEnd class in back_end/base.py. This class
implements the KMD protocol (see the doc-strings for details). Three methods
read, write and flush must be defined on-top of the base's definitions. These
should read/write/flush bytes coming from or going to the device.

The back-end may emit various exceptions all derived from
exceptions.BackEndError. These exceptions are checked/caught by the system's
interface, all other exceptions may bubble up to the user in nasty ways. Make
sure all back-ends catch and re-cast all exceptions which may appear to a user
during (ab)normal use.


System Interface
----------------

The system interface is designed to tie together a back-end with its
architecture and produce a cleaner interface to the device. This interface is
used by the GUI for all device interactions. The system interface is defined by
the System class in system.py. In general, the interfaces provided by the
system function by examining the architecture model and then taking action
communicating with the back-end.

Because the features provided by the class are fairly diverse, it is split up
into several mix-ins. These mix-in classes are designed to be inherited into the
System to provide various useful features. These mix-ins are described in the
doc-string at the top of system.py.

By convention, accesses to the back-end should not fail but rather return dummy
data. This vastly reduces the complexity of the GUI code and improves the user's
experience in the event that the board goes down temporarily.

Device
``````
The device mix-in (device.py) provides cleaner access to the back-end.  GUI code
should not directly access the back-end and should instead use this interface.
This interface is thread-safe and, because it is slow, should be accessed from a
background thread to prevent the GUI from blocking.

By convention, if a value cannot be accessed, -1 is provided instead.

Unfortunately this interface is not yet complete and should be extended as
required.

Expression Evaluator
````````````````````
An expression evaluator is provided which allows valid Python expressions to be
evaluated and the result used. Within the expression evaluator many variables
are defined providing access to the system being debugged. This facility is
designed for use by the GUI to allow users to input expressions involving, for
example, register values and calculations.

The expression evaluator exposes registers as variables with names corresponding
to those defined in the system architecture. It also exposes the system's
memories as standard python array-like objects. Values are fetched as needed by
the user's expression. This is implemented using some scary-looking python hacks
(defined in util/lazy.py) which allow the creation of variables whose value is
not calculated until it is needed.

Note that while this facility uses eval (the root of all evil), the functions
and objects available to the evaluator are limited such that usage should be
safe.

Logger
``````
To collect non-critical errors and warnings a logging facilities are
implemented. The log is a list of Exceptions and may be displayed to the user.
Exceptions are added to the log using the log method. This takes the exception
and a boolean indicating whether the error is important. Important errors are
ones which it is deemed appropriate to display to the user immediately, for
example, upon invalid data being entered by the user.


GUI + Glue
----------

The GUI is defined in terms of a number of specialised widgets which are defined
in the view package (in the directory of the same name). These widgets provide
complex UI elements such as memory viewers and control bars. These widgets are
finally instantiated in a main window in main.py. In the future this should be
made into a more flexible system where the UI is easily configured by the user
rather than just being a fixed layout.

Conventions
```````````

Numbers should be described in the same format that would be accepted by the
expression evaluator. An unfortunate side-effect of this is that hex and binary
numbers are presently shown with the 0x and 0b prefixes.

Numbers should generally be specified in hex and padded to the correct width
with zeros. In this case, the function format_number in the format module
(view/format.py) should be used to generate appropriate strings.

Unprintable ASCII values are shown as a dot.

Error dialogues are annoying. Instead, errors should be reported to the system
log which should be displayed to the user in a non-disruptive way and only
highlighted for critical errors or in cases where the user may be trying to
learn by trial-and-error (for example when using the expression evaluator).

Not a convention but a forewarning to the uninitiated developer: gtk.TreeViews
are very useful (as GTK's only real table-style viewer) but are a bit abstract.
It is well-worth taking a look at the PyGTK manual and a good number of examples
before you start working with them.


Widgets
```````

All complex widgets should accept a system model and behave sensibly in
isolation without any further glue-code. This design was chosen because it
greatly simplifies the code required and keeps code relating to presentation and
interaction close together.

Widgets should provide a refresh method which will cause the widget to
re-request any data it is displaying from the system.

The main widgets which have been defined so far are described below.

ControlBar
~~~~~~~~~~
The ControlBar (view/control_bar.py) provides a GTK ToolBar which features
buttons for controlling the code assembly, memory loading and  execution of the
device.

LogViewer
~~~~~~~~~
The LogViewer (view/log.py) provides a log-viewer for system errors. New errors
are briefly highlighted when they arrive. The widget emits an "update" signal
when a new log entry is added which can be used to show the log viewer when
important (flagged) log items appear.

Register Viewer
~~~~~~~~~~~~~~~
The register viewer shows each register bank in its own page of a gtk.Notebook.
Register banks are displayed as a gtk.TreeView of all the integer registers and
a second gtk.Notebook of bit-field viewers for the bit-fields. The
BitFieldViewer provides an interface for editing a bit field as described in the
Architecture model.

Memory Viewer
~~~~~~~~~~~~~
The memory viewer provides a way to view and modify the contents of a memory in
the system. This is probably the most complex and also most messy widget in the
system. The viewer features a toolbar with an address box (which accepts
expressions) which is used to change the address being viewed. The follow
check-box allows the window to follow the result of the expression as its result
changes (for example if the expression contains a register's value). The viewer
also provides options for the style of display including whether or not
addresses should be aligned appropriately. Finally, the widget contains a large
gtk.TreeView which can be infinitely scrolled and edited as required.

Because gtk.TreeView cannot lazily load its contents let-alone allow the display
of extremely large numbers of items, special measures were needed to implement
the memory viewer. This works by calculating the number of rows which would fit
into the viewer and then creating just enough rows to fill the display without
scrolling. These rows are then populated with values from memory offset as
appropriate to give the appearance of scrolling.

The data which is inserted into the TreeView is generated by MemoryTable objects
(from view/_memory_table.py). By creating suitable MemoryTables, different views
of the memory can be defined. MemoryTables define the columns of data in the
view and provide functions for requesting and setting the values of these
columns. The interface required of a MemoryTable is described by the MemoryTable
base class.

To deal with the special-case of variable-length instruction-set compilers,
data is requested from MemoryTables in terms of the number of rows required to
fill the screen rather than a given range of memory. This allows each row to
have different lengths when variable length instructions are used.

The main memory viewer attempts to create a selection of MemoryTables which
might be useful to the user. In particular, a table for each disassembler the
Architecture provides (using a DisassemblyTable) is given along with various
groupings of CPU-words along with an ASCII decoding (using a MemoryWordTable).

The rows of the memory viewer may be annotated when, for example, a register
contains its address or if it is a breakpoint. To implement this, Annotation
objects (view/_annotation.py) are defined which can specify an icon, colouring
and additional tool-tip information for a given address. These objects are
instanciated by the get_annotation method in the MemoryTableViewer class (in
view/memory.py). As breakpoints etc. are not currently implemented, only
register pointers are displayed as annotations.


RunInBackground Decorator
`````````````````````````

To prevent the GUI from becoming blocked when communicating with the device.
Because GTK only allows access to its functions from within the main program/GTK
thread, this means putting communication logic in a separate thread and sending
the results to the GUI thread for display. To make this as painless as possible,
a python decorator is provided which abstracts awway the grimy details.

The following examples (which use a made-up api for example purposes) show how
the decorator might be used. Full documentation on the decorator and how it
works can be found in view/background.py.

Health Warning
~~~~~~~~~~~~~~
This feature makes use of a number of relatively advanced Python features.
Having said this, it should be safe to use the feature as shown in the examples
and as seen in the code without having to understand how it works behind the
scenes.

Most visibly it is a semi-abuse of the Python 'generator' feature. If
you are not familliar with Python's generator syntax you should note that
"yield" is a key word used by generators and has nothing inherently to do
with threading.

It also exposes a few oddities in the way that decorators work which mean that
some things may seem a bit strange/arbitrary if you're not familliar with the
intricacies of how decorators and classes/methods interact in Python.

Google or look at the docs for generators and decorators to find out more. If
you're feeling keen, jump down the rabbit hole and take a look at the
implementation. The implementation is heavily commented and tries not to leave
out explanation when unusual features are used. Don't be too put off :).

Example 1:
~~~~~~~~~~
A method which fetches some data from the board (a slow process) and then
updates the GUI::

	class MyClass(object):
		
		...
	
		@RunInBackground()
		def update_view(self, addr):
			# The function starts execution in its own thread
			
			# Read a value from the board. This function blocks for some time before
			# returning a value. Note: this operation must be thread-safe.
			value = read_from_board(addr)
			
			# Once all work is done in the thread, execution is switched to the GTK thread
			# by yielding.
			yield
			
			# Update the widget directly (this is allowed as we're in the GTK thread).
			self.widget.set_value(value)

When update_view is called it will return instantly and execution of the method
body will begin in a separate thread. It will execute in this thread until it
yields. It will then be inserted into the GTK main-loop idle queue and, when the
GTK main loop picks it up, will safely continue execution in the GTK main thread.

Example 2:
~~~~~~~~~~
A method which checks something in the GUI and uses the result to fetch some
data from the board (a slow process) and then updates the GUI::

	class MyClass(object):
		
		...
	
		@RunInBackground(start_in_gtk = True)
		def update_view_from_gui(self):
			# Because start_in_gtk is True, the function starts execution in the GTK
			# thread so we can safely access the value of a widget
			try:
				addr = int(self.addr_box.get_text())
			except ValueError, e:
				# If the user entered something that didn't make sense, log the error
				log_error(e)
				
				# By returning before we yield we terminate the call early and execution
				# does not continue in another thread.
				return
			
			yield
			# Now we've yielded, we continue execution in a background thread as in
			# example 1.
			
			# Read a value from the board at the address we just read out of a text-box.
			value = read_from_board(addr)
			
			# Once all work is done in the thread, execution is switched to the GTK thread
			# by yielding.
			yield
			
			# Update the widget directly (this is allowed as we're in the GTK thread).
			self.widget.set_value(value)

This example is similar to example 1 except that execution initially starts in
the GTK main thread and only enters the background thread when we yield. From
then on it behaves the same allowing us to yield once more in the background
thread to re-enter the GTK main thread.

One other detail is that in the event of a value error we can return and stpo
the function continuing. This may also be used while in the background thread or
at any other time to halt execution of the function.


Example 3:
~~~~~~~~~~
A method which takes a very long time to execute and displays its progress in a
progress bar::

	class MyClass(object):
		
		def __init__(self):
			
			...
			
			# We get the gtk.Adjustment object which represents the progress of the
			# function decorated by load_memory_image_decorator by requesting it for
			# this instance of MyClass from the decorator. (Note the slightly usual
			# way you must request this).
			adjustment = MyClass.load_memory_image_decorator(self)
			
			# Set a progress bar's adjutment object to the adjustment corresponding to
			# this method. This adjustment will be updated as the method executes and
			# the progress bar will be automatically redrawn by GTK to show this, no
			# further code required!
			self.progressbar.set_adjustment(adjustment)
		
		
		...
		
		
		# load_memory_image_decorator is a (static) refrence to a RunInBackground
		# decorator which is interrogated to retrieve a gtk.Adjustment which
		# contains progress information.
		load_memory_image_decorator = RunInBackground()
		
		# We decorate the method with the update_with_progress_decorator object we
		# created above
		@load_memory_image_decorator
		def load_memory_image(self, image_file):
			# Execution begins in a background thread
			
			# Go through the image file, address-by-address...
			num_entries = len(image_file)
			for entry_num, (addr, value) in enumerate(image_file.get_data()):
				# ...and write the value to the board
				write_to_board(addr, value)
				
				# To indicate the progress of the operation, yield a tuple containing
				# the entry number we're up to and the number of entries in total. This
				# will not cause execution to leave the background thread but will cause
				# an update to the gtk.Adjustment and thus the progress bar in the GUI.
				yield (entry_num, num_entries)
			
			# Once all work is done in the thread we do an empty yield which finally
			# returns us to the GTK thread. This action also resets the gtk.Adjustment
			# to zero (i.e. resets the progress bar).
			yield
			
			# Upade the display to reflect newly loaded data
			self.update_display()

In this example, a gtk.Adjustment (gtk-speak for an object containing the data
to be displayed in, for example, a progress bar) is retrieved from the decorator
and passed to a progress bar.

While in a background thread you can yield (current_progress, max_progress) tuples to
indicate your progress through a long-running task. Whenever a tuple such as
this is yeilded, the process is not placed in a background task but continues to
run in the background thread. Instead, the values returned are used to set the
values of the gtk.Adjustment so that the progressbar attached updates
accordingly.

Once the background thread has finished, an empty yield causes the execution to
continue in the GTK thread as-per-usual. You can only yield progress updates
while in the background thread.

Note that every time a progress update is yieleded a call to update the
adjustment is added to the GTK idle queue. As a result you should be careful not
to generate these updates too fast otherwise the system will spend most of its
time redrawing the progress bar!
