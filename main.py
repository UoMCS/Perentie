#!/usr/bin/env python

"""
Debugger GUI main executable.
"""

import pygtk, gtk, glib, gobject

from back_end import EmulatorBackEnd, SerialPortBackEnd
from system   import System

from view.register         import RegisterViewer
from view.memory           import MemoryViewer
from view.control_bar      import ControlBar
from view.progress_monitor import ProgressMonitor
from view.log              import LogViewer
from view.peripherals      import get_peripheral_view


class Main(gtk.Window):
	
	# Number of ms between screen refreshes
	REFRESH_INTERVAL = 300
	
	def __init__(self, system):
		"""
		A quick-and-simple main debugger window containing a control bar, register
		viewer, two memory viewers and a log viewer.
		"""
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		
		self.system = system
		
		# Set the window title
		self.set_title("%s Debugger (%s)"%(
			self.system.architecture.name, self.system.back_end.name
		))
		
		# Default window size
		self.set_default_size(900, 650)
		
		self.vbox = gtk.VBox()
		self.add(self.vbox)
		
		# Add the control bar
		self.control_bar = ControlBar(self.system)
		self.vbox.pack_start(self.control_bar, expand = False, fill = True)
		
		# Add a movable division between the register and memory viewers
		self.hpaned = gtk.HPaned()
		self.vbox.pack_start(self.hpaned, expand = True, fill = True)
		
		# Add a register viewer
		self.register_viewer = RegisterViewer(self.system)
		self.hpaned.pack1(self.register_viewer, shrink = False)
		
		# Add a movable division between the two memory viewers
		self.vpaned = gtk.VPaned()
		self.hpaned.pack2(self.vpaned, shrink = False)
		
		# Add two memory viewers (one defaulting to a disassembly, one not)
		memory = self.system.architecture.memories[0]
		self.memory_viewers = []
		self.memory_viewers.append(MemoryViewer(self.system, memory, True))
		self.memory_viewers.append(MemoryViewer(self.system, memory, False))
		
		# Show memory viewers in frames
		f1 = gtk.Frame()
		f2 = gtk.Frame()
		f1.add(self.memory_viewers[0])
		f2.add(self.memory_viewers[1])
		f1.set_shadow_type(gtk.SHADOW_OUT)
		f2.set_shadow_type(gtk.SHADOW_OUT)
		self.vpaned.pack1(f1, resize = True, shrink = False)
		self.vpaned.pack2(f2, resize = True, shrink = False)
		
		# Add a progress monitor for long-running background functions
		self.progress_monitor = ProgressMonitor(self.system)
		self.progress_monitor.add_adjustment(
			ControlBar.loader_background_decorator.get_adjustment(self.control_bar),
			"Loading Memory Image"
			)
		self.vbox.pack_start(self.progress_monitor, expand=False, fill=True)
		
		# Add an expander with a log viewer in
		self.unread_log_entries = 0
		self.log_expander = gtk.Expander("Error Log")
		self.log_viewer   = LogViewer(self.system)
		self.log_expander.add(self.log_viewer)
		self.log_viewer.connect("update", self._on_log_update)
		self.log_expander.connect("activate", self._on_log_update, None)
		self.log_expander.set_use_markup(True)
		self.vbox.pack_start(self.log_expander, expand = False, fill = True)
		
		# Get peripherals
		for periph_num, (periph_id, periph_sub_id) in enumerate(self.system.get_peripheral_ids()):
			viewer = get_peripheral_view(periph_id, periph_sub_id)
			if viewer is not None and viewer[1] is not None:
				name, view_class = viewer
				periph_widget = view_class(self.system, periph_num, periph_id, periph_sub_id)
				
				# Create a window to display the widget
				periph_window = gtk.Window()
				periph_window.add(periph_widget)
				periph_window.set_title(periph_widget.get_name())
				periph_window.set_icon(periph_widget.get_icon(gtk.ICON_SIZE_MENU))
				periph_window.set_default_size(350, 250)
				
				# Add toolbar button to show the window
				def show_periph_window(button):
					periph_window.show_all()
					periph_window.present()
				self.control_bar.add_peripheral(periph_widget, show_periph_window)
				
				# Add progress monitors
				for adjustment, name in periph_widget.get_progress_adjustments():
					self.progress_monitor.add_adjustment(adjustment, name)
		
		# Interval at which to auto refresh the UI's contents
		glib.timeout_add(Main.REFRESH_INTERVAL, self._on_interval)
		
		# Kill comms on GTK mainloop exit
		gtk.quit_add(0, self.system.kill_device_comms)
		
		self.connect("destroy", gtk.main_quit)
	
	
	def _on_interval(self):
		"""
		Callback called at a regular interval. Update the screen.
		"""
		self.system.clear_cache()
		
		self.register_viewer.refresh()
		for memory_viewer in self.memory_viewers:
			memory_viewer.refresh()
		self.control_bar.refresh()
		
		# Reschedule the interval
		return True
	
	
	def _on_log_update(self, widget, flag):
		"""
		Called when a new log item appears. If it is flagged, expand the log viewer.
		"""
		if flag:
			self.log_expander.set_expanded(True)
		
		if self.log_expander.get_expanded():
			# Viewer expanded
			self.unread_log_entries = 0
		else:
			if flag is not None: # Flag is none on activate
				self.unread_log_entries += 1
		
		
		if self.unread_log_entries > 0:
			self.log_expander.set_label("<b>Error Log (%d)</b>"%self.unread_log_entries)
		else:
			self.log_expander.set_label("Error Log")


if __name__=="__main__":
	# Enable GTK multi-threading support
	gtk.gdk.threads_init()
	
	from optparse import OptionParser, OptionGroup
	parser = OptionParser()
	
	ser = OptionGroup(parser, "Serial Device Options",
	                  "Options relating to the use of an serial device back-end.")
	ser.add_option("-s", "--serial", dest = "serial_port",
	               action="store", type="string", default = 0,
	               help = "Use the specified serial device as the back-end")
	ser.add_option("-b", "--baud-rate", dest = "baudrate",
	               action="store", type="int", default = 115200,
	               help = "Baudrate of the serial connection")
	parser.add_option_group(ser)
	
	emu = OptionGroup(parser, "Emulator Options",
	                  "Options relating to the use of an emulator back-end.")
	emu.add_option("-e", "--emulator",
	               dest = "emulator", action="store_true", default = False,
	               help = "Use an emulator back-end")
	parser.add_option_group(emu)
	
	# Parse arguments
	import sys
	options, args = parser.parse_args(sys.argv)
	
	if options.emulator:
		# Emulator is passed the remaining arguments
		back_end = EmulatorBackEnd(args[1:])
	else:
		back_end = SerialPortBackEnd(options.serial_port, options.baudrate)
	
	# Create the main window & system
	main_window = Main(System(back_end))
	main_window.show_all()
	
	# GTK Mainloop
	gtk.main()
