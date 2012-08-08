#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A GTK+ widget for viewing a system's memory.
"""


from math      import ceil

import gtk, gobject, glib

from pixmaps import *
from format  import *

from background import RunInBackground

from _memory_table import MemoryWordTable, DisassemblyTable
from _annotation   import RegisterAnnotation


def xxx_allowed_element_sizes(word_bits):
	"""
	XXX: Bodge to allow working with back-end protocol
	Returns the list of all allowed multiples of this word's size which can be
	requested as an element
	"""
	
	out = []
	num = 1
	while num*word_bits <= 64:
		out.append(num)
		num += 1
	
	return out


class MemoryViewer(gtk.VBox):
	
	__gsignals__ = {
		# Emitted when the memory viewer has made a modification to memory
		'edited': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
	}
	
	def __init__(self, system, memory, show_disassembly = True):
		"""
		A memory viewing/editing tool for the specified memory in the given system.
		
		If show_disassembly is True, the initial memory table will be a disassembly,
		otherwise it will be a single-CPU-word memory table and failing that, a
		single memory word.
		"""
		gtk.VBox.__init__(self, homogeneous = False)
		
		self.system = system
		self.memory = memory
		
		# The address to follow (if required)
		self.addr_expression = ""
		
		# Important types of table (indexes into self.memory_tables) set by
		# _create_memory_tables
		self.table_disassembly = None
		self.table_cpu_word    = None
		
		# Initialise the list of memory tables viewable
		self._create_memory_tables()
		
		# Add the main toolbar
		self._add_toolbar()
		
		# Add the memory table viewer
		self.memory_table_viewer = MemoryTableViewer(self.system, self.memory)
		self.pack_start(self.memory_table_viewer, expand = True, fill = True)
		self.memory_table_viewer.show()
		
		# Hook everything up
		self.view_combo_box.connect("changed", self._on_view_changed)
		self.align_check.connect("toggled", self._on_align_toggled)
		self.follow_check.connect("toggled", self._on_follow_toggled)
		self.addr_box.connect("activate", self._on_addr_change)
		
		self.memory_table_viewer.connect("scrolled", self._on_scroll)
		self.memory_table_viewer.connect("edited", self._on_edited)
		
		# Work out the default table to show
		if show_disassembly and self.table_disassembly is not None:
			# Show a disassembly if possible
			table = self.table_disassembly
		elif self.table_cpu_word is not None:
			# Show a cpu word if possible
			table = self.table_cpu_word
		else:
			# Otherwise just show whatever we've got
			table = 0
		
		# Select the default table
		self.view_combo_box.set_active(table)
		self.memory_table_viewer.set_memory_table(self.memory_tables[table][1])
	
	
	def _create_memory_tables(self):
		"""
		Create/define the memory tables (models of memory data in table form) for
		each required view.
		"""
		
		self.memory_tables = []
		
		# Add each disassembler supported by the memory
		for (assembler, disassembler) in self.memory.assemblers:
			# If no disassembly table has been selected, chose this one (the first)
			if self.table_disassembly is None:
				self.table_disassembly = len(self.memory_tables)
			
			self.memory_tables.append(("Disassembly (%s)"%disassembler.name,
			                          DisassemblyTable(self.system,
			                                           self.memory,
			                                           assembler, disassembler)))
		
		# Names of element sizes which may be displayed
		size_names = {}
		
		# Element sizes specific to this memory's architecture
		size_names[self.memory.word_width_bits] = "Memory-Word"
		
		# Element sizes specific to this CPU architecture
		size_names[self.system.architecture.word_width_bits / 2] = "Half-Word"
		size_names[self.system.architecture.word_width_bits * 1] = "Word"
		size_names[self.system.architecture.word_width_bits * 2] = "Double-Word"
		size_names[self.system.architecture.word_width_bits * 4] = "Quad-Word"
		
		# Generic names (taking priority over arch specific names)
		size_names[1] = "Bit"
		size_names[4] = "Nybble"
		size_names[8] = "Byte"
		
		
		# For each allowed element size in words, add a number of multiples
		for elem_size_words in xxx_allowed_element_sizes(self.memory.word_width_bits):
			
			# Don't print un-named sizes
			elem_size_bits = elem_size_words * self.memory.word_width_bits
			if elem_size_bits not in size_names:
				continue
			
			# Separator
			if len(self.memory_tables) > 0:
				self.memory_tables.append(("", None))
			
			# Get the human-friendly size name
			size_name = size_names[elem_size_bits]
			
			# If no CPU-word memory table has been selected, use this one if it is
			if size_name == "Word" and self.table_cpu_word is None:
				self.table_cpu_word = len(self.memory_tables)
			
			
			for num_elems in [1,2,4,8,16]:
				self.memory_tables.append(("%d %s%s (%d × %d = %d Bits)"%(
				                             num_elems,
				                             size_name,
				                             "" if num_elems == 1 else "s",
				                             num_elems,
				                             elem_size_bits,
				                             num_elems * elem_size_bits),
				                          MemoryWordTable(self.system,
				                                          self.memory,
				                                          elem_size_words,
				                                          num_elems)))
	
	def _add_toolbar(self):
		"""
		Generate the toolbar of the memory viewer.
		"""
		self.toolbar = gtk.HBox(homogeneous = False, spacing = 5)
		
		# Address entry label
		entry_label = gtk.Label("Address:")
		self.toolbar.pack_start(entry_label, expand = False, fill=True)
		entry_label.show()
		
		# Address entry box
		self.addr_box = gtk.Entry()
		self.addr_box.set_tooltip_text("Address to be shown")
		self.toolbar.pack_start(self.addr_box, expand = False, fill=True)
		self.addr_box.show()
		
		# Follow check box
		self.follow_check = gtk.CheckButton("Follow")
		self.follow_check.set_tooltip_text("Follow the address as it changes")
		self.follow_check.set_active(False)
		self.toolbar.pack_start(self.follow_check, expand = False, fill=True)
		self.follow_check.show()
		
		# Align
		self.align_check = gtk.CheckButton("Align")
		self.align_check.set_tooltip_text("Align the address appropriately for the current view")
		self.align_check.set_active(True)
		self.toolbar.pack_start(self.align_check, expand = False, fill=True)
		self.align_check.show()
		
		# View selection combo (seperators represented by empty strings)
		self.view_combo_box = gtk.combo_box_new_text()
		self.view_combo_box.set_tooltip_text("Type of view")
		def row_sep(m, i):
			return m.get(i,0)[0] == ""
		self.view_combo_box.set_row_separator_func(row_sep)
		
		# Add the word sizes
		map(self.view_combo_box.append_text, (name for name,_ in self.memory_tables))
		
		self.toolbar.pack_end(self.view_combo_box, expand = False, fill=True)
		self.view_combo_box.show()
		
		self.toolbar.show()
		self.pack_start(self.toolbar, expand = False, fill=True, padding=5)
	
	
	def _on_view_changed(self, view_combo_box):
		"""
		Called when the user selects a new view.
		"""
		view_num = self.view_combo_box.get_active()
		self.memory_table_viewer.set_memory_table(self.memory_tables[view_num][1])
		self.refresh()
	
	
	def _on_align_toggled(self, align_check):
		"""
		Toggle alignment for all the memory tables
		"""
		align = self.align_check.get_active()
		
		for _, memory_table in self.memory_tables:
			if memory_table is not None:
				memory_table.set_align(align)
		
		self.refresh()
	
	
	def _on_follow_toggled(self, follow_check):
		"""
		When follow mode is toggled, refresh the display incase it now needs to jump
		to the followed value
		"""
		self.refresh()
	
	
	def _on_addr_change(self, addr_box):
		"""
		When the address is entered, jump to it and refresh the display. Try
		enabling follow mode.
		"""
		self.addr_expression = addr_box.get_text()
		self.follow_check.set_active(True)
		self.refresh()
	
	
	def _on_scroll(self, memory_viewer):
		self.follow_check.set_active(False)
	
	
	def evaluate_addr_expression(self):
		"""
		Evaluate the saved addr_expression and set the address accordingly.
		"""
		try:
			addr = self.system.evaluate(self.addr_expression)
			self.memory_table_viewer.set_addr(addr)
		except Exception, e:
			# Disable follow mode if it has been enabled
			self.follow_check.set_active(False)
			self.system.log(e, True)
	
	
	def _on_edited(self, memory_viewer):
		"""
		The memory has been edited.
		"""
		self.emit("edited")
	
	
	@RunInBackground(start_in_gtk = True)
	def refresh(self):
		"""
		Update the memory displayed.
		"""
		# Get the checkbox in the gtk thread
		follow = self.follow_check.get_active()
		
		
		yield
		# Evaluate the address if we're following it in a background thread
		if follow:
			self.evaluate_addr_expression()
		
		# Return to the GTK thread to update the view
		yield
		self.memory_table_viewer.refresh()



class MemoryTableViewer(gtk.Table):
	
	__gsignals__ = {
		# Emitted when a memory location is edited
		'edited':   (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
		
		# Emitted when the window is scrolled (and thus the address displayed
		# changes)
		'scrolled': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
	}
	
	# Special Columns in the ListStore
	ICON_COLUMN    = 0 # The icon for the row
	COLOUR_COLUMN  = 1 # The row's foreground colour
	TOOLTIP_COLUMN = 2 # The row's tool-tip
	ADDR_COLUMN    = 3 # The address of the row
	DATA_COLUMN    = 4 # The first column containing data from the memory table
	
	
	# Max scroll speed (scroll 2**MAX_SCROLL_SPEED every 100ms)
	MAX_SCROLL_SPEED = 16
	
	# The rate at which scrolling accelerates depending on scrollbar position
	SCROLL_ACCELERATION_FACTOR = 0.8
	
	
	def __init__(self, system, memory):
		"""
		An viewer/editor for memory-table models.
		
		XXX: Because GTK doesn't provide an infinately scrollable TreeView, this
		widget has some fairly grubby work-arounds to approximate that behaviour. In
		particular, it uses a list-view of a number of rows which completely fills
		the widget which are then modified in order to give the appearence of
		scrolling.
		"""
		gtk.Table.__init__(self, 2,2)
		
		self.system = system
		self.memory = memory
		
		# The table to display
		self.memory_table = None
		
		# The address this memory_table_viewer attempting to show on its first row
		self.addr = 0
		
		# The length of each row (i.e. the number of addresses covered) used for
		# scrolling. At least 1.  For MemoryTables with hetrogenous row sizes, this
		# number should be the size of the first row.
		self.addr_step = 1
		
		# The row of the tree_view currently being edited (this row must not be
		# updated otherwise it will kill the editor).
		self.editing_row = None
		
		# A dictionary relating addresses to lists of Annotation objects.
		self.annotations = {}
		
		# The TreeModel into which data will be inserted for display by the
		# treeview. Initially contains a single empty row which is used for
		# measuring the height of a row in the table.
		self.list_store = gtk.ListStore(gtk.gdk.Pixbuf, str, str, str)
		self._add_empty_row()
		
		# The treeview and model used to display memory elements. The size request
		# is zeroed so it becomes scrollable.
		self.tree_view = gtk.TreeView(self.list_store)
		self.tree_view.set_enable_search(False)
		self.tree_view.set_size_request(0,0)
		self.attach(self.tree_view, 0,1, 0,1, gtk.EXPAND | gtk.FILL, gtk.EXPAND | gtk.FILL)
		self.tree_view.show()
		
		# Add the globally-present address column
		self._init_addr_column()
		
		# Add the scrollbars. This is done manually so that the vertical scrollbar
		# can be hacked.
		self.vadjustment = gtk.Adjustment()
		self.hscrollbar  = gtk.HScrollbar(self.tree_view.get_hadjustment())
		self.vscrollbar  = gtk.VScrollbar(self.vadjustment)
		
		self.attach(self.hscrollbar, 0,1, 1,2, gtk.FILL, gtk.FILL)
		self.attach(self.vscrollbar, 1,2, 0,1, gtk.FILL, gtk.FILL)
		
		self.hscrollbar.show()
		self.vscrollbar.show()
		
		# Initalise the infinate scrollbar
		self._init_vscrollbar()
		
		# Handle size changes
		self.connect("size-allocate", self._on_size_change)
		
		self.refresh()
	
	
	def _add_empty_row(self):
		"""
		Adds an empty row to the list store.
		"""
		cols = [""] * (self.list_store.get_n_columns() - self.DATA_COLUMN)
		self.list_store.append([POINTER_DEFAULT, "#000000", "Loading...", ""] + cols)
	
	
	def _get_row_height(self):
		"""
		Get the size of a row in the table.
		XXX: Strictly speaking rows may all be of different sizes so this isn't
		correct. In this case, however, all rows are of uniform size because no
		multi-line fields are used.
		"""
		# Get the size of the first cell
		first_column = self.tree_view.get_column(0)
		first_cell   = self.tree_view.get_background_area(0, first_column)
		
		return first_cell.height
	
	
	def _get_visible_height(self):
		"""
		Find the height of the table row-viewing area
		"""
		if self.tree_view.get_bin_window() is not None:
			return self.tree_view.get_bin_window().get_geometry()[3]
		else:
			return 10
	
	
	def _get_num_visible_rows(self):
		"""
		Get the number of rows which will currently be visible. At least one row
		will be shown.
		"""
		return max(1, self._get_visible_height() / self._get_row_height())
	
	
	def _on_size_change(self, *args):
		"""
		Recalculate as needed for the new size of the window
		"""
		# Hide horizontal scrollbar when not needed
		adj = self.tree_view.get_hadjustment()
		scroll_needed = adj.get_upper() != adj.get_value() + adj.get_page_size()
		if scroll_needed:
			self.hscrollbar.show()
		else:
			self.hscrollbar.hide()
		
		# Get the number of rows which are off the screen
		delta_rows = len(self.list_store) - self._get_num_visible_rows()
		
		if delta_rows < 0:
			# More rows needed
			for row in range(-delta_rows):
				self._add_empty_row()
			
			self.refresh()
		
		elif delta_rows > 0:
			# Remove excess rows
			it = self.list_store.iter_nth_child(None, len(self.list_store) - delta_rows)
			while self.list_store.remove(it): pass
	
	
	def _init_vscrollbar(self):
		self.vadjustment.set_all(
			value= -0.1,
			lower=-1.1, upper=1.1,
			step_increment=0.02, page_increment=0.2,
			page_size=0.2
		)
		
		# Is the scrollbar currently scrolling?
		self.scrolling = False
		
		# How far has been scrolled?
		self.distance = 0.0
		
		self.vscrollbar.connect("button-press-event",   self._on_vscrollbar_start)
		self.vscrollbar.connect("button-release-event", self._on_vscrollbar_end)
		
		self.vadjustment.connect("value-changed", self._on_vadjustment_changed)
		
		self.vscrollbar.connect("scroll-event", self._on_scroll_event)
		self.tree_view.connect("scroll-event",  self._on_scroll_event)
	
	
	def _on_vscrollbar_start(self, vscrollbar, event):
		"""
		Event when the scrollbar starts scrolling
		"""
		self.scrolling = True
		glib.timeout_add(100, self._on_scroll_tick)
		
		# Reset the distance scrolled and the original address
		self.distance           = 0.0
		self.addr_before_scroll = self.get_addr()
		
		self.emit("scrolled")
	
	
	def _on_vscrollbar_end(self, vscrollbar, event):
		"""
		Event when the scrollbar stops scrolling
		"""
		# Do one last scroll tick (also ensures at least one is carried out)
		self._on_scroll_tick()
		
		# Stop scrolling
		self.scrolling = False
		self._on_vadjustment_changed()
	
	
	def _on_vadjustment_changed(self, vadjustment = None):
		"""
		Reset the scrollbar to the center of the bar unless the user is actively
		scrolling.
		"""
		if not self.scrolling:
			self.vadjustment.set_value(-self.vadjustment.get_page_size()/2)
	
	
	def _on_scroll_event(self, widget, event):
		"""
		While scrolling using the mouse
		"""
		down  = event.direction == gtk.gdk.SCROLL_DOWN
		up    = event.direction == gtk.gdk.SCROLL_UP
		
		if up:
			delta = -self.addr_step
		elif down:
			delta =  self.addr_step
		
		self.addr += delta
		# The row being edited may have moved, stop editing!
		self.editing_row = None
		
		self.emit("scrolled")
		
		self.refresh()
	
	
	def _on_scroll_tick(self):
		"""
		While scrolling, repeatedly call this function to actually do the scroll
		"""
		# Stop ticking after the scrolling stops
		if not self.scrolling:
			return False
		
		# Get value of the scrollbar's center
		value   = self.vadjustment.get_value()
		value  += self.vadjustment.get_page_size() / 2
		
		# Apply the acceleration factor (as between -1 and 1 this just means
		# applying a power (and ensuring the sign is the same)
		sign    = (int(value >= 0) * 2) - 1
		value   = abs(value)
		value **= MemoryTableViewer.SCROLL_ACCELERATION_FACTOR
		value  *= sign
		
		# Scale up to the scroll speed
		value  *= MemoryTableViewer.MAX_SCROLL_SPEED
		
		# Calculate the amount to jump
		delta  = 2**abs(value)
		
		# Scale down due to this being called every 100ms not every second
		delta /= 10.0
		
		# Update the scroll distance
		if   value > 0: self.distance += delta
		elif value < 0: self.distance -= delta
		
		# Round to the largest magnitude
		sign = (int(self.distance >= 0) * 2) - 1
		rounded_distance = int(ceil(abs(self.distance))) * sign
		
		# Update address
		self.set_addr(self.addr_before_scroll + rounded_distance)
		
		# The row being edited may have moved, stop editing!
		self.editing_row = None
		
		self.emit("scrolled")
		
		self.refresh()
		
		return True
	
	
	def _init_addr_column(self):
		"""
		Adds the address column
		"""
		col = gtk.TreeViewColumn("Address")
		
		# Create an icon (for pointer arrows, etc)
		icon_renderer = gtk.CellRendererPixbuf()
		col.pack_start(icon_renderer, expand = False)
		
		# Create a text area for the address
		text_renderer = gtk.CellRendererText()
		text_renderer.set_property("editable", False)
		text_renderer.set_property("font", "monospace")
		col.pack_start(text_renderer, expand = True)
		
		# Assign the column's renderers to the TreeModel's columns containing their
		# data and colour info
		col.add_attribute(icon_renderer, "pixbuf",     MemoryTableViewer.ICON_COLUMN)
		
		col.add_attribute(text_renderer, "text",       MemoryTableViewer.ADDR_COLUMN)
		col.add_attribute(text_renderer, "foreground", MemoryTableViewer.COLOUR_COLUMN)
		
		self.tree_view.append_column(col)
	
	
	def set_addr(self, addr):
		"""
		Change the address this window is displaying.
		"""
		if self.addr != addr:
			# Stop editng as we've moved
			self.editing_row = None
			
			self.addr = addr
	
	
	def get_addr(self):
		return self.addr
	
	
	def set_memory_table(self, memory_table):
		# Stop editing
		self.editing_row = None
		
		# Remove the columns and list store used by the previous table
		if self.memory_table is not None:
			# Remove the old model
			self.tree_view.set_model()
			self.list_store = None
			
			# Remove the columns (except the address column)
			for column in self.tree_view.get_columns()[1:]:
				self.tree_view.remove_column(column)
		
		self.memory_table = memory_table
		
		# Get the columns provided by the memory table
		column_names = self.memory_table.get_columns()
		
		# Create a model containing columns for the icon, address, row-colour and
		# each of the columns in this memory_table
		self.list_store = gtk.ListStore(*([
			gtk.gdk.Pixbuf,                  # Icon
			str,                             # Colour
			str,                             # Toolip-text
			str,                             # Address
			] + ([str] * len(column_names)))) # Data from the memory table (as strings)
		
		# Ensure there is at least one row (for display calculations)
		self._add_empty_row()
		
		# Create columns for each data table entry
		for num, column_name in enumerate(column_names):
			# Create a column with the given name
			col = gtk.TreeViewColumn(column_name)
			
			# Add an editable text renderer
			renderer = gtk.CellRendererText()
			renderer.set_property("editable", True)
			renderer.set_property("font", "monospace")
			col.pack_start(renderer, expand = True)
			
			# Set up callbacks for the editing events
			renderer.connect("editing-started",  self._on_editing_started)
			renderer.connect("editing-canceled", self._on_editing_canceled)
			renderer.connect("edited",           self._on_edited, num)
			
			# Set the column of data to display in the row's colour
			col.add_attribute(renderer, "text",       MemoryTableViewer.DATA_COLUMN + num)
			col.add_attribute(renderer, "foreground", MemoryTableViewer.COLOUR_COLUMN)
			
			# Add the column
			self.tree_view.append_column(col)
		
		self.tree_view.set_model(self.list_store)
		self.tree_view.set_tooltip_column(MemoryTableViewer.TOOLTIP_COLUMN)
	
	
	def _on_editing_started(self, renderer, editable, path):
		"""
		Called when the user starts editing a cell.
		"""
		# The user has started editing this row. Do not update it!
		# XXX: GTK states path may be an integer or a tuple with an int in. I don't
		# know how to force it to be one of these but it happens to be a string
		# here...
		self.editing_row = int(path)
	
	
	def _on_editing_canceled(self, renderer):
		"""
		Called when a cell was being edited but the attempt was canceled.
		"""
		self.editing_row = None
		
		# Refresh to ensure the row is updated after being locked for editing
		self.refresh()
	
	
	@RunInBackground()
	def _on_edited(self, renderer, path, new_data, column):
		"""
		Called when a cell's value has been changed.
		"""
		# XXX: GTK states path may be an integer or a tuple with an int in. I don't
		# know how to force it to be one of these but it happens to be a string
		# here...
		row = int(path)
		
		# Write back the change
		self.memory_table.set_cell(self.get_addr(), row, column, new_data)
		
		# Return to GTK thread
		yield
		
		self.editing_row = None
		
		self.emit("edited")
		
		# Refresh to show what value is now actually in that location
		self.refresh()
	
	
	def _refresh_annotation_data(self):
		"""
		Fetch annotation data from the system
		XXX: TODO add breakpoints and watchpoints
		"""
		# Clear existing annotations
		self.annotations = {}
		
		# For each register defined as a pointer into this memory...
		register_pointers = self.system.get_register_pointers(self.memory)
		for register_bank, register in register_pointers:
			# Place an annotation at the value it points to
			value = self.system.read_register(register)
			annotation = RegisterAnnotation(self.system, self.memory,
			                                value, register_bank, register)
			self.annotations.setdefault(value,[]).append(annotation)
	
	
	def get_annotation(self, addr_start, length):
		"""
		Return an (icon, colour, tooltip) for the given address
		"""
		
		# Get the end address of the location to annotate and also calculate the
		# version as if it had been aliased
		addr_end        = addr_start + length
		addr_end_masked = addr_end & ((1<<self.memory.addr_width_bits) - 1)
		
		# The address wraps around if when masked it is different
		addr_wraps = addr_end != addr_end_masked
		
		all_annotations = []
		
		# Look for annotations which land in the range
		for addr, annotations in self.annotations.iteritems():
			if addr_wraps:
				if addr < addr_end_masked or addr > addr_start:
					all_annotations.extend(annotations)
			else:
				if addr_start <= addr < addr_end:
					all_annotations.extend(annotations)
		
		if all_annotations:
			max_annotation = max(all_annotations, key=(lambda a: a.get_priority()))
			
			# Use the icon from the annotation with the highest priority
			icon   = max_annotation.get_pointer_pixbuf()
			colour = max_annotation.get_colour()
			
			# Add all annotations' tooltips (in order of address)
			tooltip = "\n".join(a.get_tooltip() for a in sorted(all_annotations,
			                                                    key=(lambda a: a.addr)))
			
			return (icon, colour, tooltip)
		else:
			# No annotations:
			return (POINTER_DEFAULT, "#000000", "")
		
	
	@RunInBackground()
	def refresh(self):
		# Do nothing if no memory table has been set
		if self.memory_table is None:
			return
		
		self._refresh_annotation_data()
		
		# Fetch data from memory
		num_rows = len(self.list_store)
		memory_table_data = self.memory_table.get_data(self.get_addr(), num_rows)
		
		# Run remainder in GTK thread
		yield
		
		# Upadte address step size
		self.addr_step = memory_table_data[0][1]
		
		# Add data from memory to the list store
		for row, (addr, length, data) in enumerate(memory_table_data):
			# Format the start (and end address) of the line
			formatted_addr = format_number(addr, self.memory.addr_width_bits)
			formatted_end  = format_number(addr + length, self.memory.addr_width_bits)
			
			# The text in the address column (show the range if there is one)
			if length > 1:
				addr_col = "%s:%s"%(formatted_addr, formatted_end)
			else:
				addr_col = formatted_addr
			
			# Do not update the row if it is being edited unless its address has
			# changed
			old_addr_col = self.list_store[row][MemoryTableViewer.ADDR_COLUMN]
			if self.editing_row == row and addr_col == old_addr_col:
				continue
			
			icon, colour, annotation_tooltips = self.get_annotation(addr, length)
			
			tooltip = "<b>%s<tt>[%s]</tt></b> — %d Word%s (%d × %d = %d Bits)\n%s"%(
			                                        self.memory.name,
			                                        addr_col,
			                                        length,
			                                        "" if length == 1 else "s",
			                                        length,
			                                        self.memory.word_width_bits,
			                                        length * self.memory.word_width_bits,
			                                        annotation_tooltips)
			
			# Set the cell contents
			self.list_store[row][MemoryTableViewer.ICON_COLUMN]    = icon
			self.list_store[row][MemoryTableViewer.COLOUR_COLUMN]  = colour
			self.list_store[row][MemoryTableViewer.TOOLTIP_COLUMN] = tooltip.strip()
			self.list_store[row][MemoryTableViewer.ADDR_COLUMN]    = addr_col
			for num, datum in enumerate(data):
				self.list_store[row][MemoryTableViewer.DATA_COLUMN + num] = datum
