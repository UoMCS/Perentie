#!/usr/bin/env python

"""
A GTK+ status bar for controling a system.
"""


import gtk

from background import RunInBackground

from progress_monitor import ProgressMonitor


class StatusBar(gtk.VBox):
	
	STATUS_CODES = {
		-1  : "Communication Error", # STATUS_ERROR
		0x00: "Reset",               # STATUS_RESET
		0x01: "Device Not Ready",    # STATUS_BUSY
		0x40: "Stopped",             # STATUS_STOPPED
		0x41: "Breakpoint",          # STATUS_STOPPED_BREAKPOINT
		0x42: "Watchpoint",          # STATUS_STOPPED_WATCHPOINT
		0x43: "Memory Fault",        # STATUS_STOPPED_MEM_FAULT
		0x44: "Program Stopped",     # STATUS_STOPPED_PROG_REQ
		0x80: "Running",             # STATUS_RUNNING
		0x81: "Running (SWI)",       # STATUS_RUNNING_SWI
	}
	
	
	def __init__(self, system):
		"""
		A status bar for a system.
		"""
		gtk.VBox.__init__(self)
		
		self.system = system
		
		# Create a separator between us and the rest of the window
		sep = gtk.HSeparator()
		self.pack_start(sep, fill = True, expand = False)
		
		# A container for all the status entries
		self.hbox = gtk.HBox(spacing = 10)
		self.hbox.set_border_width(2)
		self.pack_start(self.hbox, fill = True, expand = False)
		
		# Current system status
		self.status_label = gtk.Label()
		self.hbox.pack_start(self.status_label, fill = True, expand = False)
		self._add_sep()
		
		# Step counter
		self.step_count_label = gtk.Label()
		self.hbox.pack_start(self.step_count_label, fill = True, expand = False)
		self._add_sep()
		
		# Show progress of background tasks
		self.progress_monitor = ProgressMonitor(self.system,
		                                        orientation = gtk.ORIENTATION_HORIZONTAL)
		self.hbox.pack_start(self.progress_monitor, fill = True, expand = True)
	
	
	def _add_sep(self):
		"""
		Add a horizontal separator to the end of the status bar
		"""
		sep = gtk.VSeparator()
		self.hbox.pack_start(sep, fill = True, expand = False)
	
	
	def add_adjustment(self, *args, **kwargs):
		# Forward to the progress_monitor
		self.progress_monitor.add_adjustment(*args, **kwargs)
	
	
	def remove_adjustment(self, *args, **kwargs):
		# Forward to the progress_monitor
		self.progress_monitor.remove_adjustment(*args, **kwargs)
	
	
	@RunInBackground()
	def refresh(self):
		status, steps_remaining, steps_since_reset = self.system.get_status()
		
		yield
		
		self.status_label.set_text(StatusBar.STATUS_CODES.get(status, "Device in Unknown State"))
		self.step_count_label.set_text("%s Step%s Since Reset%s"%(
			steps_since_reset,
			"s" if steps_since_reset != 1 else "",
			(" (%s Remaining)"%steps_remaining if steps_remaining > 0 else "")
		))
	
	
	def architecture_changed(self):
		"""
		Called when the architecture changes, deals with all the
		architecture-specific changes which need to be made to the GUI.
		"""
		# Nothing to do!
		self.refresh()

