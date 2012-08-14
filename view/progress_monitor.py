#!/usr/bin/env python

"""
A GTK+ widget which shows the progress of a running background process.
"""


from threading import Lock

import gtk, gobject, glib

from background import RunInBackground
from format import *


class ProgressMonitor(gtk.HBox):
	
	__gsignals__ = {
		# Emitted when the progress monitor starts showing the progress for some
		# background job. The name of the process is given as an argument (or None
		# if it doesn't have one).
		'started': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (str,)),
		
		# Emitted when the progress monitor finishes showing the progress for some
		# background job. The name of the process is given as an argument (or None
		# if it doesn't have one).
		'finished': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (str,)),
		
		# Emitted when the progress monitor finishes showing all running background
		# jobs.
		'finished_all': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
	}
	
	def __init__(self, system,
	             auto_hide = True,
	             orientation = gtk.ORIENTATION_VERTICAL,
	             runtime_threshold = 0.2,
	             spacing = 0):
		"""
		A progress-monitoring widget for long-running background processes which
		report their progress.
		
		system is a refrence to the system object being debugged.
		
		auto_hide indicates if progress bars should only be shown when the process
		is actually running.
		
		orientation is either gtk.ORIENTATION_VERTICAL or gtk.ORIENTATION_HORIZONTAL and indicates how the
		progress bars should be stacked.
		
		Do not show/raise the started event unless runtime_threshold seconds have
		elapsed. This prevents progress bars flashing up momentarily for quick
		processes. Set to 0 to always show.
		
		spacing is the gap between each progress bar.
		"""
		gtk.HBox.__init__(self, homogeneous = True, spacing = spacing)
		
		self.system            = system
		self.auto_hide         = auto_hide
		self.orientation       = orientation
		self.runtime_threshold = runtime_threshold
		
		# The set of active progress bars
		self.active_bars = set()
		
		# A GTK box object of the correct orientation
		if self.orientation == gtk.ORIENTATION_HORIZONTAL:
			# Just use this container, its an HBox
			self.box = self
		else:
			# XXX: Doesn't expand propperly!
			self.box = gtk.VBox(spacing = spacing)
			self.pack_start(self.box, fill = True, expand = True)
	
	
	def _delayed_show(self, adjustment, progress_bar):
		"""
		Callback after a period to show a progress bar which was previously hidden
		if it is still showing progress.
		"""
		upper = adjustment.get_upper()
		lower = adjustment.get_lower()
		value = adjustment.get_value()
		
		# The progress bar is still active, display it
		if upper - lower != 0:
			progress_bar.show()
			self.active_bars.add(progress_bar)
			self.emit("started", progress_bar.get_text())
	
	
	def _on_adjustment_changed(self, adjustment, progress_bar):
		"""
		Callback when an adjustment is changed.
		"""
		upper = adjustment.get_upper()
		lower = adjustment.get_lower()
		value = adjustment.get_value()
		
		if upper - lower != 0:
			# Display the progress bar
			fraction = float(value - lower) / float(upper-lower)
			progress_bar.set_fraction(fraction)
			
			# Alert/show if just started
			if progress_bar not in self.active_bars:
				if self.auto_hide:
					if self.runtime_threshold == 0.0:
						self._delayed_show(adjustment, progress_bar)
					else:
						glib.timeout_add(int(self.runtime_threshold*1000),
						                 self._delayed_show, adjustment, progress_bar)
				else:
					self.emit("started", progress_bar.get_text())
					self.active_bars.add(progress_bar)
		else:
			# This adjustment has finished, hide/alert if it was previously active
			if progress_bar in self.active_bars:
				self.active_bars.remove(progress_bar)
				
				if self.auto_hide:
					progress_bar.hide()
				
				if len(self.active_bars) == 0:
					self.emit("finished_all")
				
				self.emit("finished", progress_bar.get_text())
	
	
	def add_adjustment(self, adjustment, name = None):
		progress_bar = gtk.ProgressBar()
		
		# Add the name (if given)
		if name is not None:
			progress_bar.set_text(name)
		
		# Add the events to update the bar when the adjustment changes
		adjustment.connect("changed", self._on_adjustment_changed, progress_bar)
		adjustment.connect("value-changed", self._on_adjustment_changed, progress_bar)
		
		# Add to the window
		self.box.pack_start(progress_bar, expand=False, fill=True)
		
		# Show the bar, if appropriate
		if not self.auto_hide:
			progress_bar.show()
		else:
			progress_bar.hide()
			progress_bar.set_no_show_all(True)

