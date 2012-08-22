#!/usr/bin/env python

"""
A GTK+ toolbar + menu bar for controling a system.
"""


import gtk, gobject

import format

from background    import RunInBackground
from device_info   import DeviceInfoViewer
from symbol_viewer import SymbolViewer
from about         import AboutDialog


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
		
		# A widget displaying device information
		self.device_info_viewer = None
		
		# A widget showing memory symbols
		self.symbol_viewer = None
		
		# A list of widgets which are disabled when the processor is busy
		self.disabled_on_busy = []
		
		# A list of widgets which are disabled when no assemblers are available
		self.disabled_on_no_assembler = []
		
		# A list of widgets which are disabled when no loaders are available
		self.disabled_on_no_loader = []
		
		# Maps a peripheral widget to a tuple (tool_item, menu_item)
		self.periphs = {}
		
		# The keyboard shortcuts defined by this widget
		self.accelerators = gtk.AccelGroup()
		
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
		
		# Initialise enabled values
		self.architecture_changed()
	
	
	def _init_menubar(self):
		"""
		Add the menu buttons to the bar
		"""
		self.auto_refresh_button = self._make_menu_item("Auto Refresh", check = True)
		self.auto_refresh_button.connect("toggled", self._on_auto_refresh_toggled)
		device_submenu = self._make_menu((
			("Select New Target", gtk.STOCK_DISCONNECT, self._on_select_target_clicked, "<Control>n"),
			None,
			("Device Info", gtk.STOCK_INFO, self._on_info_clicked, "<Control>i"),
			None,
			("Refresh Now", gtk.STOCK_REFRESH, self._on_refresh_clicked, "F1"),
			self.auto_refresh_button,
			None,
			("Quit", gtk.STOCK_QUIT, self._on_quit_clicked, "<Control>w"),
		))
		
		device_menu = self._make_menu_item("Device")
		device_menu.set_submenu(device_submenu)
		self.menubar.append(device_menu)
		
		self.assemble_menu_btn   = self._make_menu_item("Assemble",  gtk.STOCK_CONVERT)
		self.reassemble_menu_btn = self._make_menu_item("Ressemble", gtk.STOCK_REFRESH, accelerator = "F3")
		self.load_menu_btn   = self._make_menu_item("Load Image",    gtk.STOCK_GO_DOWN)
		self.reload_menu_btn = self._make_menu_item("Reload Image", gtk.STOCK_REFRESH, accelerator = "F4")
		self.assemble_menu_btn.connect("activate",   self._on_select_source_file_clicked)
		self.reassemble_menu_btn.connect("activate", self._on_assemble_clicked)
		self.load_menu_btn.connect("activate",       self._on_select_image_file_clicked)
		self.reload_menu_btn.connect("activate",     self._on_load_clicked)
		
		self.symbol_viewer_btn = self._make_menu_item("Symbol Viewer", gtk.STOCK_GO_DOWN, accelerator = "<Control>s")
		self.symbol_viewer_btn.connect("activate", self._on_symbol_viewer_clicked)
		program_submenu = self._make_menu((
			self.assemble_menu_btn,
			self.reassemble_menu_btn,
			None,
			self.load_menu_btn,
			self.reload_menu_btn,
			None,
			self.symbol_viewer_btn
		))
		program_menu = self._make_menu_item("Program")
		program_menu.set_submenu(program_submenu)
		self.menubar.append(program_menu)
		
		self.disabled_on_no_assembler.append(self.assemble_menu_btn)
		self.disabled_on_no_assembler.append(self.reassemble_menu_btn)
		
		self.disabled_on_no_loader.append(self.load_menu_btn)
		self.disabled_on_no_loader.append(self.reload_menu_btn)
		
		self.reset_menu_btn = self._make_menu_item("Reset",
			gtk.STOCK_REFRESH, accelerator = "F2")
		self.run_menu_btn = self._make_menu_item("Run",
			gtk.STOCK_MEDIA_PLAY, accelerator = "F5")
		self.stop_menu_btn = self._make_menu_item("Stop",
			gtk.STOCK_MEDIA_STOP, accelerator =  "F6")
		self.step_menu_btn = self._make_menu_item("Step",
			gtk.STOCK_MEDIA_NEXT, accelerator =  "F7")
		self.multi_step_menu_btn = self._make_menu_item("Multi-Step",
			gtk.STOCK_MEDIA_FORWARD, accelerator =  "F8")
		self.pause_menu_btn = self._make_menu_item("Pause",
			check = True, accelerator="F9")
		
		self.reset_menu_btn.connect("activate", self._on_reset_clicked)
		self.run_menu_btn.connect("activate", self._on_run_clicked)
		self.stop_menu_btn.connect("activate", self._on_stop_clicked)
		self.step_menu_btn.connect("activate", self._on_step_clicked)
		self.multi_step_menu_btn.connect("activate", self._on_multi_step_clicked)
		self.pause_menu_btn.connect("toggled", self._on_pause_clicked)
		
		self.disabled_on_busy.append(self.reset_menu_btn)
		self.disabled_on_busy.append(self.run_menu_btn)
		self.disabled_on_busy.append(self.stop_menu_btn)
		self.disabled_on_busy.append(self.step_menu_btn)
		self.disabled_on_busy.append(self.multi_step_menu_btn)
		self.disabled_on_busy.append(self.pause_menu_btn)
		
		control_submenu = self._make_menu((
			self.reset_menu_btn,
			None,
			self.run_menu_btn,
			self.stop_menu_btn,
			None,
			self.step_menu_btn,
			self.multi_step_menu_btn,
			self.pause_menu_btn,
		))
		control_menu = self._make_menu_item("Control")
		control_menu.set_submenu(control_submenu)
		self.menubar.append(control_menu)
		
		self.base_bin_btn = self._make_menu_item("Binary", radio = True)
		self.base_oct_btn = self._make_menu_item("Octal", radio = True,
		                                         group = self.base_bin_btn)
		self.base_dec_btn = self._make_menu_item("Decimal", radio = True,
		                                         group = self.base_bin_btn)
		self.base_hex_btn = self._make_menu_item("Hexadecimal", radio = True,
		                                         group = self.base_bin_btn)
		
		self.base_bin_btn.connect("toggled", self._on_base_changed, 2)
		self.base_oct_btn.connect("toggled", self._on_base_changed, 8)
		self.base_dec_btn.connect("toggled", self._on_base_changed, 10)
		self.base_hex_btn.connect("toggled", self._on_base_changed, 16)
		
		if format.format_base   == 2:  self.base_bin_btn.set_active(True)
		elif format.format_base == 8:  self.base_oct_btn.set_active(True)
		elif format.format_base == 10: self.base_dec_btn.set_active(True)
		elif format.format_base == 16: self.base_hex_btn.set_active(True)
		
		
		self.base_prefix_btn = self._make_menu_item("Show Base Prefix", check = True)
		self.base_prefix_btn.connect("toggled", self._on_base_prefix_btn_toggled)
		self.base_prefix_btn.set_active(format.format_show_prefix)
		window_submenu = self._make_menu((
			("New Memory Viewer",   gtk.STOCK_NEW, self._on_new_memory_viewer_clicked, "<Control>m"),
			("New Register Viewer", gtk.STOCK_NEW, self._on_new_register_viewer_clicked, "<Control>r"),
			None,
			self.base_bin_btn,
			self.base_oct_btn,
			self.base_dec_btn,
			self.base_hex_btn,
			None,
			self.base_prefix_btn,
		))
		window_menu = self._make_menu_item("Window")
		window_menu.set_submenu(window_submenu)
		self.menubar.append(window_menu)
		
		self.periph_submenu = gtk.Menu()
		self.periph_menu = self._make_menu_item("Peripherals")
		self.periph_menu.set_submenu(self.periph_submenu)
		self.periph_menu.set_no_show_all(True)
		self.periph_menu.hide()
		self.menubar.append(self.periph_menu)
		
		help_submenu = self._make_menu((
			("About", gtk.STOCK_ABOUT, self._on_about_clicked),
		))
		help_menu = self._make_menu_item("Help")
		help_menu.set_submenu(help_submenu)
		self.menubar.append(help_menu)
	
	
	def _init_toolbar(self):
		"""
		Add the main buttons to the toolbar
		"""
		b = self._add_button("Reset", gtk.STOCK_REFRESH, self._on_reset_clicked,
		                     "Reset the board (F2)")
		self.disabled_on_busy.append(b)
		assemble_submenu = self._make_menu((
			("Reassemble (F3)", gtk.STOCK_CONVERT, self._on_reassemble_clicked),
			("Select Source File", gtk.STOCK_OPEN, self._on_select_source_file_clicked),
		))
		self.assemble_btn = self._add_menu_button("Assemble", gtk.STOCK_CONVERT, assemble_submenu,
		                                          self._on_assemble_clicked,
		                                          "Reassemble source file (F3)")
		load_submenu = self._make_menu((
			("Reload (F4)", gtk.STOCK_GO_DOWN, self._on_reload_clicked),
			("Select Image File", gtk.STOCK_OPEN, self._on_select_image_file_clicked),
		))
		self.load_btn = self._add_menu_button("Load", gtk.STOCK_GO_DOWN, load_submenu,
		                                      self._on_load_clicked,
		                                      "Load memory image onto device (F4)")
		
		self.disabled_on_no_assembler.append(self.assemble_btn)
		self.disabled_on_no_loader.append(self.load_btn)
		
		self._add_separator()
		
		b = self._add_button("Run", gtk.STOCK_MEDIA_PLAY, self._on_run_clicked,
		                     "Run indefinately (F5)")
		self.disabled_on_busy.append(b)
		b = self._add_button("Stop", gtk.STOCK_MEDIA_STOP, self._on_stop_clicked,
		                     "Stop and ignore remaining steps (F6)")
		self.disabled_on_busy.append(b)
		
		self._add_separator()
		
		b = self._add_button("Step", gtk.STOCK_MEDIA_NEXT, self._on_step_clicked,
		                     "Execute a single step (F7)")
		self.disabled_on_busy.append(b)
		b = self._add_button("Multi-Step", gtk.STOCK_MEDIA_FORWARD, self._on_multi_step_clicked,
		                     "Run for the specified number of steps (F8)")
		self.disabled_on_busy.append(b)
		self.pause_btn = self._add_toggle_button(
		                      "Pause", gtk.STOCK_MEDIA_PAUSE, self._on_pause_clicked,
		                      "Toggle Pause Multi-Stepping (F9)")
		self.disabled_on_busy.append(self.pause_btn)
		self.multi_step_spin = self._add_spin_box(4, 1, 1<<32, self._on_multi_step_changed,
		                   "Number of steps to execute for Multi-Step")
		self.disabled_on_busy.append(self.multi_step_spin)
		
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
	
	
	
	def _make_menu_item(self, item, icon_stock_id = None, icon = None,
	                    check = False, radio = False, group = None,
	                    accelerator = None):
		"""
		Create a MenuItem (or Radio/CheckMenuItem) with the given text and icon_stock_id.
		"""
		if accelerator is not None:
			key,mod = gtk.accelerator_parse(accelerator)
		
		# Create the menu item
		if check:
			menu_item = gtk.CheckMenuItem()
		elif radio:
			menu_item = gtk.RadioMenuItem(group)
		else:
			menu_item = gtk.ImageMenuItem()
			menu_item.set_always_show_image(True)
		
		if accelerator is not None:
			menu_item.add_accelerator("activate", self.accelerators, key,mod, gtk.ACCEL_VISIBLE)
		
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
				if len(item) == 3:
					item, icon_stock_id, callback = item
					accelerator = None
				elif len(item) == 4:
					item, icon_stock_id, callback, accelerator = item
				
				menu_item = self._make_menu_item(item, icon_stock_id,
				                                 accelerator = accelerator)
				
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
		
		# Create the spinbox
		spin = gtk.SpinButton(adj)
		spin.set_tooltip_text(tooltip)
		spin.connect("activate", callback)
		
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
		
		file_filter = gtk.FileFilter()
		file_filter.set_name("Assembly File (*.s)")
		file_filter.add_pattern("*.s")
		
		all_filter = gtk.FileFilter()
		all_filter.set_name("All Files")
		all_filter.add_pattern("*.*")
		
		selection.add_filter(file_filter)
		selection.add_filter(all_filter)
		
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
		
		# Update the symbol viewer
		if self.symbol_viewer is not None:
			self.symbol_viewer.refresh_symbols()
		
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
	
	
	def _on_multi_step_clicked(self, btn):
		"""
		Multi-Step button clicked: Execute a number of steps in the spin box
		"""
		self.multi_step_spin.update()
		self.multi_step_spin.activate()
	
	
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
	
	
	@RunInBackground(start_in_gtk = True)
	def _on_multi_step_changed(self, btn):
		num_steps = int(self.multi_step_spin.get_value_as_int())
		
		# Run in background
		yield
		
		self.system.run(num_steps, break_on_first_instruction = True)
		
		# Return to GTK thread
		yield
		
		self.emit("device-state-changed")
	
	def _on_auto_refresh_toggled(self, btn):
		self.emit("auto-refresh-toggled")
	
	
	def _on_select_target_clicked(self, btn):
		self.emit("select-target-clicked")
	
	
	def _on_symbol_viewer_clicked(self, btn):
		"""
		Show a window with an information viewer in it.
		"""
		if self.symbol_viewer is not None:
			# Raise the window if it is already open
			self.symbol_viewer.get_parent().present()
		else:
			self.symbol_viewer = SymbolViewer(self.system)
			
			window = gtk.Window()
			# XXX: Getting a refrence to the top-level main window I can't see any
			# other way of doing it than knowing how many levels of container we're
			# in...
			window.set_transient_for(self.get_parent().get_parent())
			window.add(self.symbol_viewer)
			window.set_title("Symbols")
			window.set_default_size(450, 550)
			
			def on_dismiss(widget):
				self.symbol_viewer = None
				window.destroy()
			window.connect("destroy", on_dismiss)
			
			window.show_all()
			window.present()
	
	
	def _on_info_clicked(self, btn):
		"""
		Show a window with an information viewer in it.
		"""
		if self.device_info_viewer is not None:
			# Raise the window if it is already open
			self.device_info_viewer.get_parent().present()
		else:
			self.device_info_viewer = DeviceInfoViewer(self.system)
			
			window = gtk.Window()
			# XXX: Getting a refrence to the top-level main window I can't see any
			# other way of doing it than knowing how many levels of container we're
			# in...
			window.set_transient_for(self.get_parent().get_parent())
			window.add(self.device_info_viewer)
			window.set_title("Device Information")
			window.set_default_size(450, 550)
			
			def on_dismiss(widget):
				window.destroy()
				self.device_info_viewer = None
			self.device_info_viewer.connect("dismissed", on_dismiss)
			window.connect("destroy", on_dismiss)
			
			window.show_all()
			window.present()
	
	
	def _on_about_clicked(self, btn):
		about_dialog = AboutDialog()
		# XXX: Getting a refrence to the top-level main window I can't see any
		# other way of doing it than knowing how many levels of container we're
		# in...
		about_dialog.set_transient_for(self.get_parent().get_parent())
		
		def close_dialog(*args):
			about_dialog.destroy()
		about_dialog.connect("response", close_dialog)
		about_dialog.connect("close", close_dialog)
		
		about_dialog.show_all()
	
	
	def _on_refresh_clicked(self, btn):
		self.emit("refresh-clicked")
	
	
	def _on_quit_clicked(self, btn):
		self.emit("quit-clicked")
	
	def _on_new_memory_viewer_clicked(self, btn):
		self.emit("new-memory-viewer-clicked")
	
	
	def _on_new_register_viewer_clicked(self, btn):
		self.emit("new-register-viewer-clicked")
	
	
	def _on_base_changed(self, btn, base):
		"""
		Change the base of the formatted fields
		"""
		if btn.get_active():
			format.set_base(base)
		
		self.emit("device-state-changed")
	
	def _on_base_prefix_btn_toggled(self, btn):
		"""
		Enable/disable the prefix in formatted values.
		"""
		format.set_show_prefix(btn.get_active())
		
		self.emit("device-state-changed")
	
	
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
		
		if self.device_info_viewer is not None:
			self.device_info_viewer.refresh()
	
	
	def architecture_changed(self):
		"""
		Called when the architecture changes, deals with all the
		architecture-specific changes which need to be made to the GUI.
		"""
		# Enable/disable assembly/loading buttons as appropriate
		can_assemble = False
		can_load     = False
		
		if self.system.architecture is not None:
			memories = self.system.architecture.memories
			can_load = len(memories) > 0
			can_assemble = len(sum((m.assemblers for m in memories), [])) > 0
		
		for widget in self.disabled_on_no_assembler:
			widget.set_sensitive(can_assemble)
		
		for widget in self.disabled_on_no_loader:
			widget.set_sensitive(can_load)
		
		if self.device_info_viewer is not None:
			self.device_info_viewer.architecture_changed()
		
		if self.symbol_viewer is not None:
			self.symbol_viewer.architecture_changed()
		
		self.refresh()
