#!/usr/bin/env python

"""
A GTK+ toolbar for controling a system.
"""


import gtk, gobject

from background import RunInBackground


class ControlBar(gtk.VBox):
	
	__gsignals__ = {
		# Emitted when something which might change the global state occurs
		# indicating a global refresh would be a good idea.
		"device-state-changed": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
		
		# Actions which are to be carried out by the MainWindow
		"auto-refresh-toggled": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
		"select-target-clicked": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
		"refresh-clicked": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
		"quit-clicked": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
		"new-memory-viewer-clicked": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
		"new-register-viewer-clicked": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
	}
	
	def __init__(self, system):
		"""
		A control bar for a system.
		"""
		gtk.VBox.__init__(self)
		
		self.system = system
		
		# A list of widgets which are disabled when the processor is busy
		self.disabled_on_busy = []
		
		# Maps a peripheral widget to a tuple (tool_item, menu_item)
		self.periphs = {}
		
		# Add the menubar
		self.menubar = gtk.MenuBar()
		self._init_menubar()
		self.pack_start(self.menubar, fill = True, expand = False)
		self.menubar.show()
		
		# Add the toolbar
		self.toolbar = gtk.Toolbar()
		self._init_toolbar()
		self.pack_start(self.toolbar, fill = True, expand = False)
		self.toolbar.show()
	
	
	def _init_menubar(self):
		"""
		Add the menu buttons to the bar
		"""
		self.auto_refresh_button = self._make_menu_item("Auto Refresh", check = True)
		self.auto_refresh_button.connect("toggled", self._on_auto_refresh_toggled)
		device_submenu = self._make_menu((
			("Select Target",  gtk.STOCK_CONNECT,     self._on_select_target_clicked),
			None,
			("Device Info",    gtk.STOCK_INFO,        self._on_info_clicked),
			None,
			("Refresh Now",    gtk.STOCK_REFRESH,     self._on_refresh_clicked),
			self.auto_refresh_button,
			None,
			("Quit",           gtk.STOCK_QUIT,        self._on_quit_clicked),
		))
		
		device_menu = self._make_menu_item("Device")
		device_menu.set_submenu(device_submenu)
		self.menubar.append(device_menu)
		
		program_submenu = self._make_menu((
			("Assemble", gtk.STOCK_CONVERT, self._on_select_source_file_clicked),
			("Reassemble", gtk.STOCK_REFRESH, self._on_assemble_clicked),
			None,
			("Load Image", gtk.STOCK_GO_DOWN, self._on_select_image_file_clicked),
			("Reload Image", gtk.STOCK_REFRESH, self._on_load_clicked),
		))
		program_menu = self._make_menu_item("Program")
		program_menu.set_submenu(program_submenu)
		self.menubar.append(program_menu)
		
		
		self.pause_menu_btn = self._make_menu_item("Pause", check = True)
		self.pause_menu_btn.connect("toggled", self._on_pause_clicked)
		control_submenu = self._make_menu((
			("Reset", gtk.STOCK_REFRESH, self._on_reset_clicked),
			None,
			("Run", gtk.STOCK_MEDIA_PLAY, self._on_run_clicked),
			("Stop", gtk.STOCK_MEDIA_STOP, self._on_stop_clicked),
			None,
			("Step", gtk.STOCK_MEDIA_NEXT, self._on_step_clicked),
			("Multi-Step", gtk.STOCK_MEDIA_FORWARD, self._on_multi_step_clicked),
			self.pause_menu_btn,
		))
		control_menu = self._make_menu_item("Control")
		control_menu.set_submenu(control_submenu)
		self.menubar.append(control_menu)
		
		window_submenu = self._make_menu((
			("New Memory Viewer",   gtk.STOCK_NEW, self._on_new_memory_viewer_clicked),
			("New Register Viewer", gtk.STOCK_NEW, self._on_new_register_viewer_clicked),
		))
		window_menu = self._make_menu_item("Window")
		window_menu.set_submenu(window_submenu)
		self.menubar.append(window_menu)
		
		# The separator before the peripherals
		self.periph_submenu = gtk.Menu()
		self.periph_menu = self._make_menu_item("Peripherals")
		self.periph_menu.set_submenu(self.periph_submenu)
		self.periph_menu.set_no_show_all(True)
		self.periph_menu.hide()
		self.menubar.append(self.periph_menu)
	
	
	def _init_toolbar(self):
		"""
		Add the main buttons to the toolbar
		"""
		b = self._add_button("Reset", gtk.STOCK_REFRESH, self._on_reset_clicked,
		                     "Reset the board")
		self.disabled_on_busy.append(b)
		assemble_submenu = self._make_menu((
			("Reassemble", gtk.STOCK_CONVERT, self._on_reassemble_clicked),
			("Select Source File", gtk.STOCK_OPEN, self._on_select_source_file_clicked),
		))
		self._add_menu_button("Assemble", gtk.STOCK_CONVERT, assemble_submenu,
		                      self._on_assemble_clicked,
		                      "Assemble source file")
		load_submenu = self._make_menu((
			("Reload", gtk.STOCK_GO_DOWN, self._on_reload_clicked),
			("Select Image File", gtk.STOCK_OPEN, self._on_select_image_file_clicked),
		))
		self._add_menu_button("Load", gtk.STOCK_GO_DOWN, load_submenu,
		                      self._on_load_clicked,
		                      "Load memory image onto device")
		
		self._add_separator()
		
		b = self._add_button("Run", gtk.STOCK_MEDIA_PLAY, self._on_run_clicked,
		                     "Run indefinately")
		self.disabled_on_busy.append(b)
		b = self._add_button("Stop", gtk.STOCK_MEDIA_STOP, self._on_stop_clicked,
		                     "Stop and ignore remaining steps")
		self.disabled_on_busy.append(b)
		
		self._add_separator()
		
		b = self._add_button("Step", gtk.STOCK_MEDIA_NEXT, self._on_step_clicked,
		                     "Execute a single step")
		self.disabled_on_busy.append(b)
		b = self._add_button("Multi-Step", gtk.STOCK_MEDIA_FORWARD, self._on_multi_step_clicked,
		                     "Run for the specified number of steps")
		self.disabled_on_busy.append(b)
		b = self.pause_btn = self._add_toggle_button(
		                      "Pause", gtk.STOCK_MEDIA_PAUSE, self._on_pause_clicked,
		                      "Toggle Pause Multi-Stepping")
		self.disabled_on_busy.append(b)
		b = self.multi_step_spin = self._add_spin_box(4, 1, 1<<32, self._on_multi_step_changed,
		                   "Number of steps to execute for Multi-Step")
		self.disabled_on_busy.append(b)
		
		# Show text and icons
		self.toolbar.set_style(gtk.TOOLBAR_BOTH)
		
		# The separator before the peripherals
		self.periph_sep = self._add_separator()
		self.periph_sep.set_no_show_all(True)
		self.periph_sep.hide()
		
		# Make all buttons homogeneous
		for tool in self.toolbar:
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
		self.toolbar.insert(btn, -1)
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
		self.toolbar.insert(btn, -1)
		btn.show()
		
		return btn
	
	
	
	def _make_menu_item(self, item, icon_stock_id = None, icon = None, check = False):
		"""
		Create a MenuItem (or CheckMenuItem) with the given text and icon_stock_id.
		"""
		# Create the menu item
		if check:
			menu_item = gtk.CheckMenuItem()
		else:
			menu_item = gtk.ImageMenuItem()
			menu_item.set_always_show_image(True)
		
		menu_item.set_label(item)
		
		if icon_stock_id is not None and not check:
			icon = gtk.Image()
			icon.set_from_stock(icon_stock_id, gtk.ICON_SIZE_MENU)
			icon.show()
		
		if icon is not None:
			menu_item.set_image(icon)
			
		return menu_item
	
	
	def _make_menu(self, items):
		"""
		Make a GTK Menu with (item, icon_stock_id, callback) pairs.
		"""
		menu = gtk.Menu()
		
		for item in items:
			if item is None:
				menu.append(gtk.SeparatorMenuItem())
			elif type(item) is tuple:
				item, icon_stock_id, callback = item
				
				menu_item = self._make_menu_item(item, icon_stock_id)
				
				# Add callback and add to the menu
				menu_item.connect("activate", callback)
				menu_item.show()
				menu.append(menu_item)
			else:
				item.show()
				menu.append(item)
		
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
		self.toolbar.insert(btn, -1)
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
		self.toolbar.insert(tool, -1)
		tool.show()
		
		return spin
	
	
	def _add_separator(self):
		sep = gtk.SeparatorToolItem()
		self.toolbar.insert(sep, -1)
		sep.show()
		return sep
	
	
	def add_periph(self, periph_widget, callback):
		"""
		Add a button for the given peripheral widget with the click event connected
		to the provided callback.
		"""
		self.periph_sep.show()
		self.periph_menu.show()
		
		# Add to toolbar
		icon = gtk.Image()
		icon.set_from_pixbuf(periph_widget.get_icon(gtk.ICON_SIZE_LARGE_TOOLBAR))
		icon.show()
		tool_item = self._add_button(periph_widget.get_short_name(),
		                             None, callback,
		                             periph_widget.get_name(),
		                             icon = icon)
		
		# Add to menubar
		icon = gtk.Image()
		icon.set_from_pixbuf(periph_widget.get_icon(gtk.ICON_SIZE_MENU))
		icon.show()
		menu_item = self._make_menu_item(periph_widget.get_name(),
		                                 icon = icon)
		menu_item.connect("activate", callback)
		menu_item.show()
		self.periph_submenu.append(menu_item)
		
		# Store a refrence to the toolbar and menu items
		assert(periph_widget not in self.periphs)
		self.periphs[periph_widget] = (tool_item, menu_item)
	
	
	def remove_periph(self, periph_widget):
		"""
		Remove the given periph_widget's menu/toolbar entries
		"""
		tool_item, menu_item = self.periphs[periph_widget]
		del self.periphs[periph_widget]
		
		# Remove the toolbar item
		self.toolbar.remove(tool_item)
		tool_item.destroy()
		
		# Remove the menu item
		self.periph_submenu.remove(menu_item)
		menu_item.destroy()
		
		# If that was the last periph, hide the seperators/menus
		if not self.periphs:
			self.periph_sep.hide()
			self.periph_menu.hide()
	
	
	@RunInBackground()
	def _on_reset_clicked(self, btn):
		self.system.reset()
		
		# Return to GTK thread
		yield
		
		self.emit("device-state-changed")
	
	
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
		self.emit("device-state-changed")
	
	
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
		
		# Start displaying progress
		yield (0,1)
		
		for progress in self.system.load_image_():
			from time import sleep
			yield progress
		
		# Return to the GTK thread
		yield
		
		self.emit("device-state-changed")
	
	
	def _on_select_image_file_clicked(self, btn):
		selection = gtk.FileChooserDialog("Select image file", None,
		                                  gtk.FILE_CHOOSER_ACTION_OPEN,
		                                  (gtk.STOCK_CANCEL, gtk.RESPONSE_CANCEL,
		                                   gtk.STOCK_OPEN, gtk.RESPONSE_OK)
		)
		
		formats = ["*%s"%f for f in self.system.get_loader_formats()]
		
		file_filter = gtk.FileFilter()
		file_filter.set_name("Image File (%s)"%(", ".join(formats)))
		for f in formats:
			file_filter.add_pattern(f)
		
		all_filter = gtk.FileFilter()
		all_filter.set_name("All Files")
		all_filter.add_pattern("*.*")
		
		selection.add_filter(file_filter)
		selection.add_filter(all_filter)
		
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
		
		self.emit("device-state-changed")
	
	
	@RunInBackground()
	def _on_stop_clicked(self, btn):
		"""
		Stop button clicked: Stop the device
		"""
		self.system.stop()
		
		# Return to GTK thread
		yield
		
		self.emit("device-state-changed")
	
	
	@RunInBackground()
	def _on_step_clicked(self, btn):
		"""
		Step button clicked: Execute a single step.
		"""
		self.system.run(1, break_on_first_instruction = False)
		
		# Return to GTK thread
		yield
		
		self.emit("device-state-changed")
	
	
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
		
		self.emit("device-state-changed")
	
	
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
		
		self.emit("device-state-changed")
	
	
	def _on_multi_step_changed(self, btn):
		# Do nothing
		pass
	
	def _on_auto_refresh_toggled(self, btn):
		self.emit("auto-refresh-toggled")
	
	
	def _on_select_target_clicked(self, btn):
		self.emit("select-target-clicked")
	
	
	def _on_info_clicked(self, btn):
		info_string  = ""
		info_string += "<b>Architecture</b>:\n"
		info_string += "  %s\n"%(
			self.system.architecture.name
			if self.system.architecture is not None
			else "<i>(Unknown)</i>")
		info_string += "  ID/Sub-ID: %02X/%04X)\n"%(
			self.system.cpu_type,
			self.system.cpu_subtype)
		info_string += "  Target Type: %s\n"%self.system.back_end.name
		info_string += "\n"
		
		info_string += "<b>Register Banks:</b>\n"
		if self.system.architecture is not None:
			for register_bank in self.system.architecture.register_banks:
				info_string += "  %s (aka <i>%s</i>):\n"%(
					register_bank.name,
					", ".join(register_bank.names[1:]),
				)
				for register in register_bank.registers:
					info_string += "    %d-bit %s Register %s (aka <i>%s</i>)\n"%(
						register.width_bits,
						"Integer" if register.bit_field is None else "Bit-Field",
						register.name,
						", ".join(register.names[1:]),
					)
		else:
			info_string += "  <i>(Unknown)</i>\n"
		info_string += "\n"
		
		info_string += "<b>Memories:</b>\n"
		if self.system.architecture is not None:
			for memory in self.system.architecture.memories:
				info_string += "  %s (aka <i>%s</i>):\n"%(
					memory.name, ", ".join(memory.names[1:]),)
				info_string += "    %d-bit addresses\n"%(memory.addr_width_bits)
				info_string += "    %d-bit minmum-addressable blocks\n"%(memory.word_width_bits)
				info_string += "    %d blocks (%d bytes)\n"%(
					memory.size, (memory.word_width_bits * memory.size)/8)
		else:
			info_string += "  <i>(Unknown)</i>\n"
		info_string += "\n"
		
		info_string += "<b>Peripherals:</b>\n"
		if self.periphs:
			for periph_widget in self.periphs:
				info_string += "  %s (%s):\n"%(
					periph_widget.get_short_name(),
					periph_widget.get_name())
				info_string += "    Number: %d\n"%(periph_widget.periph_num)
				info_string += "    ID/Sub-ID: %02X/%04X\n"%(
					periph_widget.periph_id, periph_widget.periph_sub_id)
		else:
			info_string += "  <i>(None)</i>\n"
		
		info_dialog = gtk.MessageDialog(buttons = gtk.BUTTONS_OK)
		info_dialog.set_title("Device Info")
		info_dialog.set_markup(info_string)
		info_dialog.set_destroy_with_parent(True)
		
		info_dialog.run()
		info_dialog.destroy()
	
	
	def _on_refresh_clicked(self, btn):
		self.emit("refresh-clicked")
	
	
	def _on_quit_clicked(self, btn):
		self.emit("quit-clicked")
	
	def _on_new_memory_viewer_clicked(self, btn):
		self.emit("new-memory-viewer-clicked")
	
	
	def _on_new_register_viewer_clicked(self, btn):
		self.emit("new-register-viewer-clicked")
	
	
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
		
		self.pause_menu_btn.handler_block_by_func(self._on_pause_clicked)
		self.pause_menu_btn.set_active(paused)
		self.pause_menu_btn.handler_unblock_by_func(self._on_pause_clicked)
	
	
	@RunInBackground()
	def _refresh_busy(self):
		"""
		If the processor is busy, disable the control buttons.
		"""
		status, _, _ = self.system.get_status()
		
		is_busy = status == self.system.STATUS_BUSY
		
		# Run in GTK thread
		yield
		
		# Update the pause button
		for widget in self.disabled_on_busy:
			widget.set_sensitive(not is_busy)
	
	
	def refresh(self):
		self._refresh_pause_btn()
		self._refresh_busy()
	
	
	def architecture_changed(self):
		"""
		Called when the architecture changes, deals with all the
		architecture-specific changes which need to be made to the GUI.
		"""
		# Nothing to do! The peripheral buttons are updated externally.
		self.refresh()
