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
	             loiter = 0.5,
	             spacing = 0):
		"""
		A progress-monitoring widget for long-running background processes which
		report their progress.
		
		system is a refrence to the system object being debugged.
		
		auto_hide indicates if progress bars should only be shown when the process
		is actually running.
		
		orientation is either gtk.ORIENTATION_VERTICAL or gtk.ORIENTATION_HORIZONTAL and indicates how the
		progress bars should be stacked.
		
		Show the progress bar (at 100%) for loiter seconds after the process has
		completed.
		
		spacing is the gap between each progress bar.
		"""
		gtk.HBox.__init__(self, homogeneous = True, spacing = spacing)
		
		self.system      = system
		self.auto_hide   = auto_hide
		self.orientation = orientation
		self.loiter      = loiter
		
		# A mapping from adjustments to (progress_bar, chg_handler_id,
		# val_handler_id)
		self.adjustments = {}
		
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
	
	
	def _delayed_remove(self, adjustment, progress_bar):
		"""
		Remove the given adjustment and hide the progress_bar for a finished
		adjustment. To be called after the loiter period has elapsed.
		"""
		upper = adjustment.get_upper()
		lower = adjustment.get_lower()
		
		# Remove it if it has finished
		if upper - lower == 0:
			# This adjustment has finished, hide/alert if it was previously active
			if progress_bar in self.active_bars:
				self.active_bars.remove(progress_bar)
				
				if self.auto_hide:
					progress_bar.hide()
				
				if len(self.active_bars) == 0:
					self.emit("finished_all")
				
				self.emit("finished", progress_bar.get_text())
	
	
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
					progress_bar.show()
				self.emit("started", progress_bar.get_text())
				self.active_bars.add(progress_bar)
		else:
			# The progress bar has finished, show it as 100% then hide it.
			
			# Set it to 100% if auto-hiding, otherwise just set it to 0 now as
			# otherwise it looks as if the process is still finishing off.
			if self.auto_hide:
				progress_bar.set_fraction(1)
			else:
				progress_bar.set_fraction(0)
			
			# Hide it later
			glib.timeout_add(int(self.loiter*1000),
			                 self._delayed_remove, adjustment, progress_bar)
	
	
	
	def add_adjustment(self, adjustment, name = None):
		assert(adjustment not in self.adjustments)
		
		progress_bar = gtk.ProgressBar()
		
		# Add the name (if given)
		if name is not None:
			progress_bar.set_text(name)
		
		# Add the events to update the bar when the adjustment changes
		chg_handler_id = adjustment.connect("changed", self._on_adjustment_changed, progress_bar)
		val_handler_id = adjustment.connect("value-changed", self._on_adjustment_changed, progress_bar)
		
		# Add the adjustment to the mapping
		self.adjustments[adjustment] = (progress_bar, chg_handler_id, val_handler_id)
		
		# Add to the window
		self.box.pack_start(progress_bar, expand=False, fill=True)
		
		# Show the bar, if appropriate
		if not self.auto_hide:
			progress_bar.show()
		else:
			progress_bar.hide()
			progress_bar.set_no_show_all(True)
	
	
	def remove_adjustment(self, adjustment):
		progress_bar, chg_handler_id, val_handler_id = self.adjustments[adjustment]
		
		# Disconnect signals
		adjustment.disconnect(chg_handler_id)
		adjustment.disconnect(val_handler_id)
		
		# Delete the progress bar
		self.box.remove(progress_bar)
		progress_bar.destroy()

