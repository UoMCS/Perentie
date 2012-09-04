#!/usr/bin/env python

"""
The initial program window used to select a target and then launch the
appropriate view windows.
"""

import sys, traceback
from subprocess import list2cmdline

from optparse import OptionParser, OptionGroup

import gtk, gobject

import about
from back_end import EmulatorBackEnd, SerialPortBackEnd
from system   import System

from background  import RunInBackground
from main_window import MainWindow


class Target(object):
	
	def __init__(self, target_name):
		# Name of this type of target
		self.target_name = target_name
	
	
	def add_option_group(self, parser):
		"""
		Given an optparse OptionParser, add an OptionGroup which extracts the
		arguments for the target from the command-line.
		"""
		raise NotImplementedError()
	
	
	def handle_options(self, options, args):
		"""
		Handle the options/args pair returned from the OptionParser. Return True if
		this target was specified on the command-line and thus should be chosen
		without prompting the user. Return False otherwise.
		"""
		raise NotImplementedError()
	
	
	def get_back_end(self):
		"""
		Return the back-end described by this target.
		"""
		raise NotImplementedError()


class EmulatorTarget(gtk.Table, Target):
	
	def __init__(self):
		gtk.Table.__init__(self, rows = 1, columns = 2)
		Target.__init__(self, "Emulator")
		
		# Set up the widget
		self.set_border_width(5)
		self.set_col_spacing(0, 5)
		
		label = gtk.Label("Command")
		self.attach(label, 0,1, 0,1, xoptions = gtk.FILL, yoptions = gtk.FILL)
		
		self.emulator_entry = gtk.Entry()
		self.emulator_entry.set_activates_default(True)
		self.emulator_entry.set_tooltip_text("The command (with arguments) to start the emulator.")
		self.attach(self.emulator_entry, 1,2, 0,1,
		            xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL)
	
	
	def get_emulator_command(self, option, opt_string, value, parser):
		"""
		Get all remaining arguments and treat these as the emulator string.
		"""
		parser.values.emulator = []
		while parser.rargs:
			parser.values.emulator.append(parser.rargs.pop(0))
	
	
	def add_option_group(self, parser):
		emu = OptionGroup(parser, "Emulator Options",
		                  "Options relating to the use of an emulator back-end.")
		emu.add_option("-e", "--emulator",
		               dest = "emulator", action="callback",
		               callback = self.get_emulator_command,
		               help = "Use emulator back-end specified by remaining arguments.")
		parser.add_option_group(emu)
	
	
	def handle_options(self, options, args):
		if options.emulator:
			self.emulator_entry.set_text(list2cmdline(options.emulator))
			return True
		else:
			return False
	
	
	def get_back_end(self):
		return EmulatorBackEnd(self.emulator_entry.get_text())


class SerialTarget(gtk.Table, Target):
	
	def __init__(self):
		gtk.Table.__init__(self, rows = 2, columns = 2)
		Target.__init__(self, "Serial Port")
		
		# Set up the widget
		self.set_border_width(5)
		self.set_col_spacing(0, 5)
		
		label = gtk.Label("Port")
		self.attach(label, 0,1, 0,1, xoptions = gtk.FILL, yoptions = gtk.FILL)
		
		self.serial_port_entry = gtk.Entry()
		self.serial_port_entry.set_activates_default(True)
		self.serial_port_entry.set_text("0")
		self.serial_port_entry.set_tooltip_text("Serial port the device is connected to (system default = 0)")
		self.attach(self.serial_port_entry, 1,2, 0,1,
		            xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL)
		
		label = gtk.Label("Baud-rate")
		self.attach(label, 0,1, 1,2, xoptions = gtk.FILL, yoptions = gtk.FILL)
		
		self.baudrate_entry = gtk.Entry()
		self.baudrate_entry.set_activates_default(True)
		self.baudrate_entry.set_text("115200")
		self.baudrate_entry.set_tooltip_text("Serial port speed (usually 115200)")
		self.attach(self.baudrate_entry, 1,2, 1,2,
		            xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL)
	
	
	def add_option_group(self, parser):
		ser = OptionGroup(parser, "Serial Device Options",
		                  "Options relating to the use of an serial device back-end.")
		ser.add_option("-s", "--serial", dest = "serial_port",
		               action="store", type="string", default = None,
		               help = "Use the specified serial device as the back-end")
		ser.add_option("-b", "--baud-rate", dest = "baudrate",
		               action="store", type="int", default = 115200,
		               help = "Baudrate of the serial connection")
		parser.add_option_group(ser)
	
	
	def handle_options(self, options, args):
		if options.serial_port is not None:
			self.serial_port_entry.set_text(options.serial_port)
			self.baudrate_entry.set_text(str(options.baudrate))
			return True
		else:
			return False
	
	
	def get_back_end(self):
		# Serial port might be an integer
		try:
			serial_port = int(self.serial_port_entry.get_text())
		except ValueError:
			serial_port = self.serial_port_entry.get_text()
		
		# Baudrate must be an integer
		try:
			baudrate = int(self.baudrate_entry.get_text())
		except ValueError:
			raise ValueError("Invalid baudrate (expected an integer)")
		
		return SerialPortBackEnd(serial_port, baudrate)
	


class TargetSelection(gtk.Window):
	
	TARGETS = [
		SerialTarget,
		EmulatorTarget,
	]
	
	def __init__(self, argv = None):
		"""
		A window which, when created, will prompt the user for a target and handle
		the (re-)launching of the main UI.
		
		If argv is specified, the command-line options are parsed and the dialog
		may not be shown if it isn't needed.
		"""
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		
		# The commandline option parser
		self.parser = OptionParser()
		
		self.parser.add_option("-v", "--verbose",
		                       dest = "verbose", action="store_true", default = False,
		                       help = "Show exceptions on stderr.")
		
		# The back-end and system which are being debugged
		self.back_end = None
		self.system   = None
		
		# Window used by the main GUI
		self.main_window = None
		
		# Set up the window
		self._init_gui()
		
		# Clean-up on GTK mainloop exit
		gtk.quit_add(0, self.shut_down)
		
		# Handle the command-line (must be done after show_all for notebook page to
		# be changed)
		if argv is not None:
			self.handle_argv(argv)
	
	
	def _init_gui(self):
		"""
		Set up the window
		"""
		self.set_title("Select Debugger Target")
		self.set_icon_list(*about.get_icon_list())
		self.set_default_size(400,250)
		self.set_position(gtk.WIN_POS_CENTER)
		self.set_border_width(5)
		self.connect("destroy", self._on_quit_clicked)
		
		self.vbox = gtk.VBox(spacing = 5)
		self.add(self.vbox)
		
		self.notebook = gtk.Notebook()
		self.vbox.pack_start(self.notebook, fill = True, expand = True)
		
		# Add a notebook page for each target type's configuration
		self.targets = []
		for Target in TargetSelection.TARGETS:
			target = Target()
			label = gtk.Label(target.target_name)
			self.notebook.append_page(target, label)
			
			self.targets.append(target)
		
		self.hbtns = gtk.HButtonBox()
		self.vbox.pack_start(self.hbtns, fill = True, expand = False)
		
		self.quit_btn = gtk.Button("Quit")
		self.quit_btn.connect("clicked", self._on_quit_clicked)
		self.hbtns.pack_start(self.quit_btn)
		
		self.connect_btn = gtk.Button("Connect")
		self.connect_btn.connect("clicked", self._on_connect_clicked)
		self.connect_btn.set_flags(gtk.CAN_DEFAULT)
		self.hbtns.pack_start(self.connect_btn)
		self.connect_btn.grab_default()
		
		# Press this by default if the user hits enter in some field
		
		# XXX: Line-wrapping currently doesn't fill the window width... :s
		self.error_message = gtk.Label()
		self.error_message.set_no_show_all(True)
		self.error_message.set_line_wrap(True)
		self.vbox.pack_start(self.error_message, fill = True, expand = False)
		
		self.show_all()
	
	
	def set_verbose(self, verbose):
		"""
		Possibly disable stderr.
		"""
		if not verbose:
			import sys
			class NullWriter(object):
				def write(self, data): pass
			sys.stderr = NullWriter()
	
	
	def handle_argv(self, argv):
		# Add the target's options to the parser
		for target in self.targets:
			target.add_option_group(self.parser)
		
		# The target which has been specified on the command line
		specified_target = None
		
		# Parse the options
		options, args = self.parser.parse_args(argv)
		
		# Set the verbosity of the prgoram
		self.set_verbose(options.verbose)
		
		# Deal with the target's options
		for target in self.targets:
			if target.handle_options(options, args):
				specified_target = target
		
		# If a target was specified, launch that straight away
		if specified_target is not None:
			self.notebook.set_current_page(self.targets.index(specified_target))
			self._on_connect_clicked(None)
	
	
	@RunInBackground(start_in_gtk = True)
	def _on_connect_clicked(self, widget):
		# Disable everything from the GTK thread
		self.error_message.hide()
		self.notebook.set_sensitive(False)
		self.connect_btn.set_sensitive(False)
		self.connect_btn.set_label("Connecting...")
		
		# Shut down anything already running
		self.shut_down()
		
		yield
		
		# Create the back-end/system in another thread
		try:
			target = self.targets[self.notebook.get_current_page()]
			self.back_end = target.get_back_end()
			self.system = System(self.back_end)
		except Exception, e:
			# Something failed!
			sys.stderr.write(traceback.format_exc())
			self.shut_down()
			self.error_message.set_markup("<b>Error while connecting:</b>\n%s"%str(e))
			self.error_message.show()
			pass
		
		# Return to the GTK thread
		yield
		
		# Re-enable everything
		self.notebook.set_sensitive(True)
		self.connect_btn.set_sensitive(True)
		self.connect_btn.set_label("Connect")
		
		# Can we open the main debugging window?
		if self.system is not None:
			self.start_up()
	
	
	def _on_change_target(self, window):
		"""
		Callback when a main-window requests a change of target
		"""
		self.shut_down()
		self.show()
	
	
	def start_up(self):
		"""
		Open up a main window and connect everything up for the current system.
		"""
		# Hide this window
		self.hide()
		
		# Create & show the main-window
		self.main_window = MainWindow(self.system)
		self.main_window.connect("change-target", self._on_change_target)
		self.main_window.show_all()
	
	
	def shut_down(self):
		"""
		Attempt to shut down everything that is running ready to quit or start a new
		connection.
		"""
		# Destroy the main window
		if self.main_window is not None:
			self.main_window.destroy()
			self.main_window = None
		
		# Remove the refrence to the system and kill comms threads
		if self.system is not None:
			self.system.kill_device_comms()
			self.system = None
		
		# Disconnect the back-end
		if self.back_end is not None:
			try:
				self.back_end.close()
			except Exception, e:
				sys.stderr.write("Couldn't close back_end:\n%s"%traceback.format_exc())
				pass
			self.back_end = None
	
	
	def _on_quit_clicked(self, widget = None):
		"""
		Quit the program
		"""
		self.shut_down()
		gtk.main_quit()
