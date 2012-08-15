#!/usr/bin/env python

"""
A GTK+ widget for viewing a system's registers.
"""


from threading import Lock

import gtk, gobject

from background import RunInBackground
from format import *


class RegisterViewer(gtk.Notebook):
	
	__gsignals__ = {
		# RegisterBank, Register, value
		'edited': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object, object, object)),
	}
	
	def __init__(self, system):
		"""
		A GTK widget that displays all the registers in a system. Each bank is
		displayed in its own tab of a notebook widget. Tabs are hidden for systems
		with only one register bank.
		"""
		gtk.Notebook.__init__(self)
		
		self.system = system
		
		# Tabs on the left
		self.set_tab_pos(gtk.POS_LEFT)
		
		# Only show the tabs if there's more than one
		self.set_show_tabs(len(self.system.architecture.register_banks) > 1)
		
		# Add pages for each register bank
		for register_bank in self.system.architecture.register_banks:
			label       = gtk.Label(register_bank.name)
			bank_viewer = RegisterBankViewer(self.system, register_bank)
			self.append_page(bank_viewer, label)
			
			# Connect to the edited signal for every register bank
			bank_viewer.connect("edited", self._on_register_edited, register_bank)
			
			label.show()
			bank_viewer.show()
		
		self.connect("switch-page", self._on_page_change)
		
		self.refresh()
	
	
	def _on_page_change(self, notebook, page, page_num):
		self.refresh()
	
	
	def refresh(self):
		"""
		Fetch all visible registers.
		"""
		register_bank_viewer = self.get_nth_page(self.get_current_page())
		if register_bank_viewer is not None:
			register_bank_viewer.refresh()
	
	
	def _on_register_edited(self, bank_viewer, register, new_value, register_bank):
		"""
		Call-back when a a register in any register bank has been edited.
		Re-broadcast the signal including the RegisterBank.
		"""
		self.refresh()
		self.emit("edited", register_bank, register, new_value)



class RegisterBankViewer(gtk.VBox):
	
	__gsignals__ = {
		# Register, value
		'edited': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object, object)),
	}
	
	
	def __init__(self, system, register_bank):
		"""
		A viewer for a single register bank. Shows integer registers in a editable
		list, with bit-field registers shown in a notebook below this.
		"""
		gtk.VBox.__init__(self, homogeneous = False, spacing = 0)
		
		self.system        = system
		self.register_bank = register_bank
		
		# A list of integer-value registers
		self.int_registers = []
		
		# A list of bit-field registers
		self.bit_registers = []
		
		# Divide up the registers into the bit fields and regular integers.
		for register in self.register_bank.registers:
			if register.bit_field is None:
				self.int_registers.append(register)
			else:
				self.bit_registers.append(register)
		
		self._init_int_registers()
		self._init_bit_registers()
	
	
	def _init_int_registers(self):
		"""
		Add the integer register viewer
		"""
		# The list model
		self.register_list_model = gtk.ListStore(str, str, str)
		
		# A tree view is used to display the integer registers
		self.register_list = gtk.TreeView(self.register_list_model)
		
		# Don't show a search box when typing into the register list window
		self.register_list.set_enable_search(False)
		
		# The row of the interger register being edited. This row will not be
		# refreshed to prevent the editor being killed.
		self.editing_row = None
		
		# Define the (column name, editable) in the tree view
		for column_num, (name, editable) in enumerate((("Register", False),
		                                               ("Value", True),
		                                               ("ASCII", False))):
			# Create a column with the appropriate name
			column = gtk.TreeViewColumn(name)
			
			# Register names and values are shown as (possibly editable) strings
			cell_renderer = gtk.CellRendererText()
			cell_renderer.set_property("editable", editable)
			if column_num > 0:
				cell_renderer.set_property("font", "monospace")
			
			# Set up renderer's editing events
			cell_renderer.connect("editing-started",  self._on_int_register_editing_started)
			cell_renderer.connect("editing-canceled", self._on_int_register_editing_canceled)
			cell_renderer.connect("edited",           self._on_int_register_edited)
			
			column.pack_start(cell_renderer)
			
			# Render the column column_num from the model in this column
			column.add_attribute(cell_renderer, "text", column_num)
			
			self.register_list.append_column(column)
		
		# Add the registers to the list (initially empty values)
		for register in self.int_registers:
			self.register_list_model.append((register.name, "", ""))
		
		self.pack_start(self.register_list, expand = True, fill = True)
		self.register_list.show()
	
	
	def _init_bit_registers(self):
		"""
		Add the bit-field register viewers
		"""
		self.bit_notebook = gtk.Notebook()

		for register in self.bit_registers:
			viewer = BitFieldViewer(self.system, register)
			label  = gtk.Label(register.name)
			
			viewer.connect("edited", self._on_bit_register_edited)
			
			self.bit_notebook.append_page(viewer, label)
			viewer.show()
		
		self.bit_notebook
		self.pack_start(self.bit_notebook, expand = False, fill = True)
		self.bit_notebook.show()
	
	
	def _on_int_register_editing_started(self, renderer, editable, path):
		"""
		Called when the user starts editing a cell.
		"""
		# The user has started editing this row. Do not update it!
		# XXX: GTK states path may be an integer or a tuple with an int in. I don't
		# know how to force it to be one of these but it happens to be a string
		# here...
		self.editing_row = int(path)
	
	
	def _on_int_register_editing_canceled(self, renderer):
		"""
		Called when a cell was being edited but the attempt was canceled.
		"""
		self.editing_row = None
		
		# Refresh to ensure the row is updated after being locked for editing
		self.refresh()
	
	
	@RunInBackground()
	def _on_int_register_edited(self, cell_renderer, path, new_value):
		"""
		Call-back when an integer register is edited.
		"""
		# Emit the edited event with the register and new value as arguments
		
		# Run in background
		success = False
		try:
			# XXX: GTK states path may be an integer or a tuple with an int in. I
			# don't know how to force it to be one of these but it happens to be a
			# string here...
			register = self.int_registers[int(path)]
			value    = self.system.evaluate(new_value)
			
			success = True
		except Exception, e:
			# The user entered a bad value or a comm error occurred during evaluation,
			# ignore it
			self.system.log(e, True)
		
		if success:
			self.system.write_register(register, value)
			
			# Emit the signal (in the GKT thread)
			yield
			self.editing_row = None
			if success:
				self.emit("edited", register, value)
		
	
	
	@RunInBackground()
	def _on_bit_register_edited(self, bit_field_viewer, new_value):
		"""
		Call-back when an integer register is edited.
		"""
		# Emit the edited event with the register and new value as arguments
		try:
			# XXX: GTK states path may be an integer or a tuple with an int in. I
			# don't know how to force it to be one of these but it happens to be a
			# string here...
			register = bit_field_viewer.register
			self.system.write_register(register, new_value)
			
			# Emit the signal
			yield
			self.emit("edited", register, new_value)
		except Exception, e:
			# The user entered a bad value or a comm error occurred during evaluation,
			# ignore it
			self.system.log(e)
	
	
	def set_register(self, register, value):
		"""
		Set the value of a register in the display given a register object.
		"""
		if register in self.int_registers:
			# Format the value for display
			formatted = format_number(value, register.width_bits)
			ascii     = format_ascii(value, register.width_bits)
			
			# Get the row-number
			row = self.int_registers.index(register)
			
			# Don't update the currently-edited row!
			if row == self.editing_row:
				return
			
			# Update the value in the register list
			it = self.register_list_model.get_iter(row)
			self.register_list_model.set(it, 1, formatted)
			self.register_list_model.set(it, 2, ascii)
		
		elif register in self.bit_registers:
			# Find the bit field editor
			index  = self.bit_registers.index(register)
			editor = self.bit_notebook.get_nth_page(index)
			
			# The label on the notebook
			label = self.bit_notebook.get_tab_label(editor)
			
			# Set the label tooltip to the register's value
			tt = "%s = %s"%(register.name,
			                format_number(value, register.width_bits))
			if label.get_tooltip_text() != tt:
				label.set_tooltip_text(tt)
			
			# Pass on the request to the bit-field editor
			editor.set_value(value)
	
	
	def get_register(self, register):
		"""
		Get the value of a register in the display given a register object.
		"""
		if register in self.int_registers:
			# Get the value from the list
			it = self.register_list_model.get_iter(self.int_registers.index(register))
			value = self.register_list_model.get(it, 1)
			
			return formatted_number_to_int(value)
		
		elif register in self.bit_registers:
			# Find the bit field editor
			index  = self.bit_registers.index(register)
			editor = self.bit_notebook.get_nth_page(index)
			
			# Pass on the request to the bit-field editor
			return editor.get_value()
	
	
	@RunInBackground()
	def refresh(self):
		"""
		Update all registers in this bank.
		"""
		value_assignments = {}
		for register in self.register_bank.registers:
			value_assignments[register] = self.system.read_register(register)
		
		# Update the widget in the GTK thread
		yield
		
		for register, value in value_assignments.iteritems():
			self.set_register(register, value)



class BitFieldViewer(gtk.HBox):
	
	__gsignals__ = {
		# Returns the value
		'edited': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (object, )),
	}
	
	# Size in chars of int/uint entry boxes
	ENTRY_WIDTH = 6
	
	
	def __init__(self, system, register):
		"""
		A viewer for a a single bit-field register.
		"""
		gtk.HBox.__init__(self, homogeneous = False)
		
		self.system   = system
		self.register = register
		
		self.bit_field = register.bit_field
		
		# The full value of the bit-field
		self.value = 0
		
		self.field_widgets = []
		
		# Add controls for each field
		for field_type, field_name, field in zip(self.register.bit_field.field_types,
		                                         self.register.bit_field.field_names,
		                                         self.register.bit_field.fields):
			if field_type == self.bit_field.BIT:
				# A toggle button for the bit
				widget = gtk.ToggleButton(field_name)
				
				widget.connect("toggled", self._on_change)
			
			elif field_type in (self.bit_field.INT, self.bit_field.UINT):
				# A text-box for entering integers
				widget = gtk.Entry()
				widget.set_width_chars(BitFieldViewer.ENTRY_WIDTH)
				
				widget.connect("activate", self._on_change)
			
			elif field_type == self.bit_field.ENUM:
				# A drop-down list of bit values
				widget = gtk.combo_box_new_text()
				map(widget.append_text, field[2].values())
				
				widget.connect("changed", self._on_change)
		
			# Set the tool-tip "field (regname[ranges])"
			if field_type == self.bit_field.BIT:
				ranges = "%d"%field[0]
			else:
				ranges = ", ".join(":".join(map(str,r)) for r in field[0])
			widget.set_tooltip_text("%s (%s[%s])"%(field_name, self.register.name, ranges))
			
			# Add the widget
			self.field_widgets.append(widget)
			self.pack_start(widget, expand = False, fill = True)
			widget.show()
	
	
	def decode_into_widgets(self, value):
		"""
		Set the widget's states based on the given bit-field.
		"""
		decoded_field = self.bit_field.decode(value)
		for (widget,
		     field_type,
		     field_wdith,
		     field_value,
		     field) in zip(self.field_widgets,
		                   self.bit_field.field_types,
		                   self.bit_field.field_widths,
		                   decoded_field,
		                   self.bit_field.fields):
			
			# Block the change event
			widget.handler_block_by_func(self._on_change)
			
			if field_type == self.bit_field.BIT:
				widget.set_active(field_value)
			
			elif field_type in (self.bit_field.INT, self.bit_field.UINT):
				widget.set_text(format_number(field_value, field_wdith,
				                              field_type == self.bit_field.INT))
			
			elif field_type == self.bit_field.ENUM:
				if field_value is None:
					widget.set_active(-1)
				else:
					widget.set_active(field[2].values().index(field_value))
			
			# Unblock the change event
			widget.handler_unblock_by_func(self._on_change)
		
		# Store the full value of the field
		self.value = decoded_field[-1]
	
	
	def get_widget_values(self):
		"""
		Extract the relevant value of each widget, in order.
		"""
		# Get widget contents while in the GTK thread
		widget_values = []
		for (widget,
		     field_type) in zip(self.field_widgets,
		                        self.bit_field.field_types):
			
			if field_type == self.bit_field.BIT:
				widget_values.append(widget.get_active())
			elif field_type in (self.bit_field.INT, self.bit_field.UINT):
				widget_values.append(widget.get_text())
			elif field_type == self.bit_field.ENUM:
				widget_values.append(widget.get_active())
		
		return widget_values
	
	
	def encode_from_widgets(self, widget_values, previous_value):
		"""
		Take the value of each widget and the previous value and return an integer
		containing the bit-field.
		"""
		field_values = []
		# Add the value for each widget/field
		for (widget_value,
		     field_type,
		     field_wdith,
		     field) in zip(widget_values,
		                   self.bit_field.field_types,
		                   self.bit_field.field_widths,
		                   self.bit_field.fields):
			
			if field_type == self.bit_field.BIT:
				field_values.append(widget_value)
			
			elif field_type in (self.bit_field.INT, self.bit_field.UINT):
				try:
					value = self.system.evaluate(widget_value)
				except Exception, e:
					# The user entered a bad value or a comm error occurred during evaluation,
					# ignore it
					self.system.log(e, True)
					value = 0
				field_values.append(value)
			
			elif field_type == self.bit_field.ENUM:
				if widget_value == -1:
					field_values.append(None)
				else:
					field_values.append(field[2].values()[index])
		
		# Add the previous bit-field value
		field_values.append(previous_value)
		
		return self.bit_field.encode(field_values)
	
	
	@RunInBackground(start_in_gtk = True)
	def _on_change(self, widget, *args):
		"""
		Call-back when a field has been changed
		"""
		# Get widget values while in GTK thread
		widget_values = self.get_widget_values()
		previous_value = self.value
		
		# Run in background (as we may need to evaluate something)
		yield
		value = self.encode_from_widgets(widget_values, previous_value)
		
		# Emit events from GTK thread
		yield
		# Reloading the integer value replaces all widgets with their absolute
		# values (i.e. literal values not expressions).
		self.set_value(value)
		self.emit("edited", value)
	
	
	def set_value(self, value):
		"""
		Set the value of a bit-field in the display
		"""
		self.decode_into_widgets(value)
	
	
	def get_value(self):
		"""
		Get the value of a bit-field in the display
		"""
		return self.value
