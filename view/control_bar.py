#!/usr/bin/env python

"""
A GTK+ toolbar for controling a system.
"""


import gtk

from background import RunInBackground


class ControlBar(gtk.Toolbar):
	
	def __init__(self, system):
		"""
		A control bar for a system.
		"""
		gtk.Toolbar.__init__(self)
		
		self.system = system
		
		# Flag indicating that some peripherals have been added (used to draw a
		# separator when needed.
		self.periphs_added = False
		
		self._add_button("Reset", gtk.STOCK_REFRESH, self._on_reset_clicked,
		                 "Reset the board")
		self.assemble_menu = self._make_menu((
			("Reassemble", gtk.STOCK_CONVERT, self._on_reassemble_clicked),
			("Select Source File", gtk.STOCK_OPEN, self._on_select_source_file_clicked),
		))
		self._add_menu_button("Assemble", gtk.STOCK_CONVERT, self.assemble_menu,
		                      self._on_assemble_clicked,
		                      "Assemble source file")
		self.load_menu = self._make_menu((
			("Reload", gtk.STOCK_GO_DOWN, self._on_reload_clicked),
			("Select Image File", gtk.STOCK_OPEN, self._on_select_image_file_clicked),
		))
		self._add_menu_button("Load", gtk.STOCK_GO_DOWN, self.load_menu,
		                      self._on_load_clicked,
		                      "Load memory image onto device")
		
		self._add_separator()
		
		self._add_button("Run", gtk.STOCK_MEDIA_PLAY, self._on_run_clicked,
		                 "Run indefinately")
		self._add_button("Stop", gtk.STOCK_MEDIA_STOP, self._on_stop_clicked,
		                 "Stop and ignore remaining steps")
		
		self._add_separator()
		
		self._add_button("Step", gtk.STOCK_MEDIA_NEXT, self._on_step_clicked,
		                 "Execute a single step")
		self._add_button("Multi-Step", gtk.STOCK_MEDIA_FORWARD, self._on_multi_step_clicked,
		                 "Run for the specified number of steps")
		self.pause_btn = self._add_toggle_button(
		                      "Pause", gtk.STOCK_MEDIA_PAUSE, self._on_pause_clicked,
		                      "Toggle Pause Multi-Stepping")
		self.multi_step_spin = self._add_spin_box(4, 1, 1<<32, self._on_multi_step_changed,
		                   "Number of steps to execute for Multi-Step")
		
		# Show text and icons
		self.set_style(gtk.TOOLBAR_BOTH)
		
		for tool in self:
			tool.set_homogeneous(True)
	
	
	def _add_button(self, text, icon_stock_id, callback, tooltip, icon = None):
		# Load the stock icon
		if icon is None:
			icon = gtk.Image()
			icon.set_from_stock(icon_stock_id, gtk.ICON_SIZE_LARGE_TOOLBAR)
			icon.show()
		
		# Create the button
		btn = gtk.ToolButton(icon, text)
		btn.connect("clicked", callback)
		btn.set_tooltip_text(tooltip)
		
		# Add it to the toolbar
		self.insert(btn, -1)
		btn.show()
		
		return btn
	
	
	def _add_menu_button(self, text, icon_stock_id, menu, callback, tooltip):
		# Load the stock icon
		icon = gtk.Image()
		icon.set_from_stock(icon_stock_id, gtk.ICON_SIZE_LARGE_TOOLBAR)
		icon.show()
		
		# Create the button
		btn = gtk.MenuToolButton(icon, text)
		btn.set_menu(menu)
		btn.connect("clicked", callback)
		btn.set_tooltip_text(tooltip)
		
		# Add it to the toolbar
		self.insert(btn, -1)
		btn.show()
		
		return btn
	
	
	def _make_menu(self, items):
		"""
		Make a GTK Menu with (item, callback) pairs.
		"""
		menu = gtk.Menu()
		
		for item, icon_stock_id, callback in items:
			# Load the stock icon
			icon = gtk.Image()
			icon.set_from_stock(icon_stock_id, gtk.ICON_SIZE_LARGE_TOOLBAR)
			icon.show()
			
			# Create the menu item
			menu_item = gtk.ImageMenuItem()
			menu_item.set_label(item)
			menu_item.set_image(icon)
			menu_item.set_always_show_image(True)
			
			# Add callback and add to the menu
			menu_item.connect("activate", callback)
			menu.append(menu_item)
			menu_item.show()
		
		return menu
	
	
	def _add_toggle_button(self, text, icon_stock_id, callback, tooltip):
		# Load the icon
		icon = gtk.Image()
		icon.set_from_stock(icon_stock_id, gtk.ICON_SIZE_LARGE_TOOLBAR)
		icon.show()
		
		# Create the button
		btn = gtk.ToggleToolButton()
		btn.set_label(text)
		btn.set_icon_widget(icon)
		btn.set_tooltip_text(tooltip)
		btn.connect("clicked", callback)
		
		# Add to the toolbar
		self.insert(btn, -1)
		btn.show()
		
		return btn
	
	
	def _add_spin_box(self, value, min_value, max_value, callback, tooltip):
		# Create a container for the item
		tool = gtk.ToolItem()
		
		# Create the model of the value chosen
		adj = gtk.Adjustment(value, min_value, max_value, 1, 1)
		adj.connect("value-changed", callback)
		
		# Create the spinbox
		spin = gtk.SpinButton(adj)
		spin.set_tooltip_text(tooltip)
		
		# Put the spinbox in the container
		tool.add(spin)
		spin.show()
		
		# Add the container to the toolbar
		self.insert(tool, -1)
		tool.show()
		
		return spin
	
	
	def _add_separator(self):
		sep = gtk.SeparatorToolItem()
		self.insert(sep, -1)
		sep.show()
	
	
	def add_peripheral(self, peripheral, callback):
		"""
		Add a button for the given peripheral widget with the click event connected
		to the provided callback.
		"""
		if not self.periphs_added:
			self._add_separator()
			self.periphs_added = True
		
		icon = gtk.Image()
		icon.set_from_pixbuf(peripheral.get_icon(gtk.ICON_SIZE_LARGE_TOOLBAR))
		icon.show()
		
		self._add_button(peripheral.get_short_name(),
		                 None, callback,
		                 peripheral.get_name(),
		                 icon = icon)
	
	
	@RunInBackground()
	def _on_reset_clicked(self, btn):
		self.system.reset()
		
		# Return to GTK thread
		yield
		
		self.refresh()
	
	
	def _on_assemble_clicked(self, btn):
		"""
		When the assemble button is clicked, assemble if a file is already set,
		otherwise chose a new one.
		"""
		if self.system.get_source_filename() is None:
			self._on_select_source_file_clicked(btn)
		else:
			self._on_reassemble_clicked(btn)
	
	def _on_reassemble_clicked(self, btn):
		"""
		Reassemble the current source file
		"""
		if self.system.get_source_filename() is None:
			return
		
		self.system.assemble()
		self.refresh()
	
	
	def _on_select_source_file_clicked(self, btn):
		selection = gtk.FileChooserDialog("Select source file", None,
		                                  gtk.FILE_CHOOSER_ACTION_OPEN,
		                                  (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
		                                   gtk.STOCK_OPEN, gtk.RESPONSE_OK)
		)
		
		if selection.run() == gtk.RESPONSE_OK:
			self.system.set_source_filename(selection.get_filename())
			self._on_reassemble_clicked(btn)
		
		selection.destroy()
	
	
	def _on_load_clicked(self, btn):
		"""
		When the load button is clicked, load if a file is already set,
		otherwise chose a new one.
		"""
		if self.system.get_image_filename() is None:
			self._on_select_image_file_clicked(btn)
		else:
			self._on_reload_clicked(btn)
	
	
	loader_background_decorator = RunInBackground()
	@loader_background_decorator
	def _on_reload_clicked(self, btn):
		"""
		Reload the current image file
		"""
		# Load the memory in a background thread
		if self.system.get_image_filename() is None:
			return
		
		for progress in self.system.load_image_():
			from time import sleep
			yield progress
		
		# Return to the GTK thread
		yield
		
		self.refresh()
	
	
	def _on_select_image_file_clicked(self, btn):
		selection = gtk.FileChooserDialog("Select image file", None,
		                                  gtk.FILE_CHOOSER_ACTION_OPEN,
		                                  (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
		                                   gtk.STOCK_OPEN, gtk.RESPONSE_OK)
		)
		
		if selection.run() == gtk.RESPONSE_OK:
			self.system.set_image_filename(selection.get_filename())
			self._on_reload_clicked(btn)
		
		selection.destroy()
	
	
	@RunInBackground()
	def _on_run_clicked(self, btn):
		"""
		Run button clicked: Start executing indefinately
		"""
		self.system.run()
		
		# Return to GTK thread
		yield
		
		self.refresh()
	
	
	@RunInBackground()
	def _on_stop_clicked(self, btn):
		"""
		Stop button clicked: Stop the device
		"""
		self.system.stop()
		
		# Return to GTK thread
		yield
		
		self.refresh()
	
	
	@RunInBackground()
	def _on_step_clicked(self, btn):
		"""
		Step button clicked: Execute a single step.
		"""
		self.system.run(1, break_on_first_instruction = False)
		
		# Return to GTK thread
		yield
		
		self.refresh()
	
	
	@RunInBackground(start_in_gtk = True)
	def _on_multi_step_clicked(self, btn):
		"""
		Multi-Step button clicked: Execute a number of steps in the spin box
		"""
		self.multi_step_spin.activate()
		
		# Run in background
		yield
		
		self.system.run(int(self.multi_step_spin.get_value_as_int()),
		                break_on_first_instruction = True)
		
		# Return to GTK thread
		yield
		
		self.refresh()
	
	
	@RunInBackground()
	def _on_pause_clicked(self, btn):
		"""
		Pause/unpause execution
		"""
		status, steps_remaining, steps_since_reset = self.system.get_status()
		running = status in (self.system.STATUS_RUNNING,
		                     self.system.STATUS_RUNNING_SWI)
		
		if running:
			self.system.pause_execution()
		else:
			self.system.continue_execution()
		
		# Return to GTK thread
		yield
		
		self.refresh()
	
	
	def _on_multi_step_changed(self, btn):
		# Do nothing
		pass
	
	
	@RunInBackground()
	def _refresh_pause_btn(self):
		"""
		Update the state/tooltip of the pause button
		"""
		status, steps_remaining, steps_since_reset = self.system.get_status()
		
		stopped = status in (self.system.STATUS_STOPPED,
		                     self.system.STATUS_STOPPED_BREAKPOINT,
		                     self.system.STATUS_STOPPED_WATCHPOINT,
		                     self.system.STATUS_STOPPED_MEM_FAULT,
		                     self.system.STATUS_STOPPED_PROG_REQ)
		
		# If we're stopped and there are steps remaining, we're paused
		paused = stopped and steps_remaining > 0
		
		# Run in GTK thread
		yield
		
		# Update the pause button
		self.pause_btn.handler_block_by_func(self._on_pause_clicked)
		self.pause_btn.set_active(paused)
		self.pause_btn.handler_unblock_by_func(self._on_pause_clicked)
	
	
	def refresh(self):
		self._refresh_pause_btn()
