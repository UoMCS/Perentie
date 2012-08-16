#!/usr/bin/env python

"""
The initial program window used to select a target and then launch the
appropriate view windows.
"""

import gtk, glib, gobject

from background import RunInBackground

from register         import RegisterViewer
from memory           import MemoryViewer
from control_bar      import ControlBar
from status_bar       import StatusBar
from log              import LogViewer
from peripherals      import get_peripheral_view


class MainWindow(gtk.Window):
	
	__gsignals__ = {
		# Emitted when the window is closed and a new target is being requested
		"change-target": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
	}
	
	# Number of ms between screen refreshes
	REFRESH_INTERVAL = 300
	
	def __init__(self, system):
		"""
		A main-window which contains controls, error logs, and register & memory
		viewers.
		"""
		gtk.Window.__init__(self, gtk.WINDOW_TOPLEVEL)
		
		self.system = system
		
		# Number of log entries recieved while the log-viewer was collapsed
		self.unread_log_entries = 0
		
		# A list of peripheral viewer widgets
		self.periph_viewers = []
		
		# A list of extra memory-viewer windows
		self.memory_viewers = []
		
		# A list of extra register-viewer windows
		self.register_viewers = []
		
		# A flag which can be set to kill the refresh loop
		self.killed = False
		
		# General components
		self.control_bar = ControlBar(self.system)
		self.register_viewer = RegisterViewer(self.system)
		self.log_viewer = LogViewer(self.system)
		self.status_bar = StatusBar(self.system)
		
		# Two memory viewers, one disassembly view by default, one not
		self.memory_viewer_top = MemoryViewer(self.system, True)
		self.memory_viewer_btm = MemoryViewer(self.system, False)
		
		# Propogate out refreshes when the device's state is changed
		self.control_bar.connect("device-state-changed", self._on_device_state_changed)
		self.register_viewer.connect("edited", self._on_device_state_changed)
		self.memory_viewer_top.connect("edited", self._on_device_state_changed)
		self.memory_viewer_btm.connect("edited", self._on_device_state_changed)
		
		# Calls from the control bar
		self.control_bar.connect("refresh-clicked", self._on_device_state_changed)
		self.control_bar.connect("select-target-clicked", self._on_select_target_clicked)
		self.control_bar.connect("quit-clicked", self._on_quit_clicked)
		self.control_bar.connect("new-memory-viewer-clicked", self._on_new_viewer_clicked,
		                         MemoryViewer, self.memory_viewers, "Memory Viewer")
		self.control_bar.connect("new-register-viewer-clicked", self._on_new_viewer_clicked,
		                         RegisterViewer, self.register_viewers, "Register Viewer")
		
		self._init_gui()
		self._init_adjustments()
		
		# A recurring call which is used to refresh the display
		glib.timeout_add(MainWindow.REFRESH_INTERVAL, self._on_interval)
		
		# Load up all architecture-specific stuff
		self._architecture_changed()
	
	
	def _init_gui(self):
		"""
		Set up the GUI and all its widgets!
		"""
		# Default window size
		self.set_default_size(1024, 768)
		
		vbox = gtk.VBox()
		self.add(vbox)
		
		# Add the control/menu bar
		vbox.pack_start(self.control_bar, expand = False, fill = True)
		
		# Add a movable division between the register and memory viewers
		reg_mem_panes = gtk.HPaned()
		vbox.pack_start(reg_mem_panes, expand = True, fill = True)
		
		# Add the register viewer
		reg_mem_panes.pack1(self.register_viewer, shrink = False)
		
		# Add a movable division between the two memory viewers
		mem_split = gtk.VPaned()
		reg_mem_panes.pack2(mem_split, shrink = False)
		
		# Display the memory viewers
		mem_split.pack1(self.memory_viewer_top, resize = True, shrink = False)
		mem_split.pack2(self.memory_viewer_btm, resize = True, shrink = False)
		
		# Add an expander with a log viewer in
		self.log_expander = gtk.Expander("Error Log")
		self.log_expander.add(self.log_viewer)
		self.log_expander.set_use_markup(True)
		vbox.pack_start(self.log_expander, expand = False, fill = True)
		
		# Expand the viewer if a flagged entry arrives
		self.log_viewer.connect("update", self._on_log_update)
		
		# Clear the unread counter when shown
		self.log_expander.connect("activate", self._on_log_update, None)
		
		# Add a status-bar
		vbox.pack_start(self.status_bar, fill=True, expand=False)
		
		# Tick the auto-refresh box
		self.control_bar.auto_refresh_button.set_active(True)
		
		# Quit when closing this window
		self.connect("destroy", self._on_quit_clicked)
	
	
	def _init_adjustments(self):
		"""
		Add all background process progress adjustments to the status-bar.
		"""
		
		# Memory image loading
		self.status_bar.add_adjustment(
			ControlBar.loader_background_decorator.get_adjustment(self.control_bar),
			"Loading Memory Image"
		)
	
	
	def _make_container_window(self, title, widget, icon = None, size = None):
		"""
		Make a simple window containing a widget.
		"""
		periph_window = gtk.Window()
		periph_window.set_transient_for(self)
		periph_window.add(widget)
		periph_window.set_title(title)
		if icon is not None:
			periph_window.set_icon(icon)
		if size is not None:
			periph_window.set_default_size(*size)
		
		return periph_window
	
	
	def _init_periph(self, periph_num, periph_id, periph_sub_id,
	                 name, PeripheralWidget):
		"""
		Instanciate and create a window for this peripheral viewer and hook up all
		events.
		"""
		periph_widget = PeripheralWidget(self.system, periph_num,
		                                 periph_id, periph_sub_id)
		
		self.periph_viewers.append(periph_widget)
		
		# Create a window to display the widget
		periph_window = self._make_container_window(periph_widget.get_name(),
		                                            periph_widget,
		                                            periph_widget.get_icon(gtk.ICON_SIZE_MENU))
		
		# Prevent being closed (just hide)
		def on_close(window, event):
			# Don't close the window, just hide it
			window.hide()
			return True
		periph_window.connect("delete-event", on_close)
		
		# Add toolbar button to show the window
		def show_periph_window(button):
			periph_window.show_all()
			periph_window.present()
		self.control_bar.add_periph(periph_widget, show_periph_window)
		
		# Add progress monitors
		for adjustment, name in periph_widget.get_progress_adjustments():
			self.status_bar.add_adjustment(adjustment, name)
	
	
	def _destroy_periph(self, periph_viewer):
		"""
		Destroy a periph_widget and disconnect everything.
		"""
		periph_window = periph_viewers.get_parent_window()
		
		# Disconnect all the adjustments
		adjustments = periph_window.get_progress_adjustments()
		for adjustment in adjustments:
			self.status_bar.remove_adjustment(adjustment)
		
		# Remove from the control bar
		self.control_bar.remove_periph(periph_viewer)
		
		# Close the window
		periph_window.destroy()
	
	
	@RunInBackground()
	def _update_peripherals(self):
		"""
		Update the peripheral viewers.
		"""
		# Get the periph list in another thread
		periph_ids = self.system.get_peripheral_ids()
		
		# Return to the GTK thread
		yield
		
		# A list of periph_id/periph_sub_id pairs in the same order as the list of
		# periph_viewers for lookups. Entries which have been updated are replaced
		# with None to flag them as being up-to-date.
		cur_periph_ids = [(p.periph_id, p.periph_sub_id) for p in self.periph_viewers]
		
		for periph_num, (periph_id, periph_sub_id) in enumerate(periph_ids):
			if (periph_id, periph_sub_id) in cur_periph_ids:
				# A viewer already been created for this widget, make sure its
				# peripheral number is up-to-date
				index = cur_periph_ids.index((periph_id, periph_sub_id))
				self.periph_viewers.periph_num = periph_num
				
				# Widget has been updated
				cur_periph_ids[index] = None
			else:
				# No viewer exists, create one (if possible)
				name, PeripheralWidget = get_peripheral_view(periph_id, periph_sub_id)
				if PeripheralWidget is not None:
					self._init_periph(periph_num, periph_id, periph_sub_id,
					                  name, PeripheralWidget)
		
		# Remove any old peripherals which still remain
		for index, periph_ids in list(enumerate(cur_periph_ids))[::-1]:
			# If the periph_ids has not been cleared to None, it was not updated and
			# thus the corresponding widget should be destroyed.
			if periph_ids is not None:
				periph_viewer = self.periph_viewers.pop(index)
				self._destroy_periph(periph_viewer)
	
	
	def _on_interval(self):
		"""
		Callback called at a regular interval. Update the screen.
		"""
		# Die if killed
		if self.killed:
			return False
		
		# If auto-refresh is enabled, do it!
		if self.control_bar.auto_refresh_button.get_active():
			self.refresh()
		
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
	
	
	def _on_device_state_changed(self, *args):
		"""
		Emitted whenever a change occurs to the device which may cause changes in
		all widgets and thus should force a global refresh.
		"""
		self.refresh()
	
	
	def _on_select_target_clicked(self, btn):
		"""
		Close this window and re-show the initial target selection window.
		"""
		for viewer in self.memory_viewers + self.register_viewers + self.periph_viewers:
			# XXX: Peripheral widgets don't seem to like get_parent_window...
			window = viewer.get_parent_window() or viewer.get_parent()
			window.destroy()
		
		# Stop the refresh timer
		self.killed = True
		
		self.handler_block_by_func(self._on_quit_clicked)
		self.emit("change-target")
		self.destroy()
		
	
	
	def _on_quit_clicked(self, btn):
		"""
		Quit the program, NOW!
		"""
		gtk.main_quit()
	
	
	def _on_new_viewer_clicked(self, btn, ViewerType, viewer_list, title):
		"""
		Create a new viewer in a window.
		
		ViewerType is a class which implements a viewer widget.
		
		viewer_list is a list to which the viewer widget will be added and then
		removed when the window is closed.
		
		title is a title for the window.
		"""
		viewer = ViewerType(self.system)
		
		def on_close(window, event, viewer):
			viewer_list.remove(viewer)
		
		window = self._make_container_window(title, viewer, size = (600,500))
		window.connect("delete-event", on_close, viewer)
		
		window.show_all()
		viewer.refresh()
		
		viewer_list.append(viewer)
	
	
	@RunInBackground()
	def refresh(self):
		"""
		Refresh all widgets' data
		"""
		self.system.clear_cache()
		
		# Check to see if the architecture changed
		board_changed = self.system.get_board_definition_changed()
		
		if board_changed:
			self.system.update_architecture()
		
		# Return to GTK thread
		yield
		
		if board_changed:
			self.architecture_changed()
			return
		
		# Board didn't change, just refresh as-per-usual
		self.control_bar.refresh()
		self.register_viewer.refresh()
		self.status_bar.refresh()
		self.memory_viewer_top.refresh()
		self.memory_viewer_btm.refresh()
		
		for viewer in self.memory_viewers + self.register_viewers:
			viewer.refresh()
	
	
	def _architecture_changed(self):
		"""
		Local version for just the MainWindow's own widgets. Does not propogate out.
		Called when the architecture changes, deals with all the
		architecture-specific changes which need to be made to the GUI.
		"""
		# Set the window title
		self.set_title("%sDebugger (%s)"%(
			("%s "%self.system.architecture.name
			 if self.system.architecture is not None
			 else ""),
			self.system.back_end.name
		))
		
		# Update the peripherals available
		self._update_peripherals()
		
		self.refresh()
	
	def architecture_changed(self):
		"""
		Called when the architecture changes, deals with all the
		architecture-specific changes which need to be made to the GUI.
		"""
		# Update this window's widgets
		self._architecture_changed()
		
		# Propogate to widgets
		self.control_bar.architecture_changed()
		self.register_viewer.architecture_changed()
		self.log_viewer.architecture_changed()
		self.status_bar.architecture_changed()
		self.memory_viewer_top.architecture_changed()
		self.memory_viewer_btm.architecture_changed()
		
		for viewer in self.memory_viewers + self.register_viewers:
			viewer.architecture_changed()
