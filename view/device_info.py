#!/usr/bin/env python

"""
A GTK+ widget which displays information about the connected device.
"""


import gtk, gobject

from background  import RunInBackground
from peripherals import get_peripheral_view

from format import *


class DeviceInfoViewer(gtk.VBox):
	
	__gsignals__ = {
		# Emitted when the info window is dismissed
		'dismissed': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
	}
	
	def __init__(self, system):
		"""
		A GTK widget that displays all known information about the connected system.
		"""
		gtk.VBox.__init__(self, spacing = 5)
		
		self.system = system
		
		self.set_border_width(5)
		
		# Notebook displaying all info
		self.notebook = gtk.Notebook()
		self.pack_start(self.notebook, fill = True, expand = True)
		
		# Dismiss Button
		self.button_box = gtk.HButtonBox()
		self.pack_start(self.button_box, fill = True, expand = False)
		self.dismiss_btn = gtk.Button("Dismiss")
		self.dismiss_btn.connect("clicked", self._on_dismiss_clicked)
		self.button_box.pack_start(self.dismiss_btn)
		
		self.show_all()
		
		self.architecture_changed()
	
	
	def _on_dismiss_clicked(self, btn):
		self.emit("dismissed")
	
	
	def refresh(self):
		"""
		Refreshes information in the widget.
		"""
		# Nothing to update
		pass
	
	
	def table_add_row(self, table, row, title, value):
		title_label = gtk.Label(title)
		title_label.set_alignment(0,0.5)
		value_label = gtk.Label()
		value_label.set_markup(value)
		value_label.set_alignment(0,0.5)
		table.attach(title_label, 1,2, row,row+1,
		             xoptions=gtk.FILL, yoptions=gtk.FILL)
		table.attach(value_label, 2,3, row,row+1,
		             xoptions=gtk.FILL|gtk.EXPAND, yoptions=gtk.FILL)
	
	
	def _add_basic_info_page(self):
		"""
		Adds a page to the notebook showing the system's basic info.
		"""
		
		label = gtk.Label("Basic")
		num_rows = 9
		table = gtk.Table(rows = num_rows, columns = 3)
		table.set_border_width(5)
		table.set_col_spacings(10)
		table.set_row_spacings(3)
		self.notebook.append_page(table, label)
		
		# Add an icon
		icon = gtk.Image()
		icon.set_from_stock(gtk.STOCK_DIALOG_INFO, gtk.ICON_SIZE_DIALOG)
		alignment = gtk.Alignment(0.5, 0)
		alignment.add(icon)
		table.attach(alignment, 0,1, 0,num_rows,
		             xoptions=gtk.FILL, yoptions=gtk.FILL)
		
		row = 0
		self.table_add_row(table, row, "Architecture:",
			self.system.architecture.name
			if self.system.architecture is not None
			else "<i>(Unknown)</i>")
		row += 1
		
		self.table_add_row(table, row, "Target Type:", self.system.back_end.name)
		row += 1
		
		table.attach(gtk.HSeparator(), 1,3, row,row+1,
		             xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL,
		             ypadding = 3)
		row += 1
		
		self.table_add_row(table, row, "Word Size:",
			("%d bit%s"%(self.system.architecture.word_width_bits,
			             "" if self.system.architecture.word_width_bits == 1 else "s"))
			if self.system.architecture is not None
			else "<i>(Unknown)</i>")
		row += 1
		
		if self.system.architecture is not None:
			num_registers = sum(len(b.registers)
			                    for b in self.system.architecture.register_banks)
		self.table_add_row(table, row, "Register Banks:",
			("%d (%d register%s)"%(
				len(self.system.architecture.register_banks),
				num_registers, "" if num_registers == 1 else "s"))
			if self.system.architecture is not None
			else "<i>(Unknown)</i>")
		row += 1
		
		self.table_add_row(table, row, "Memories:",
			("%d (%s)"%(
				len(self.system.architecture.memories),
				format_storage_size(sum((m.size * m.word_width_bits)
				                        for m in self.system.architecture.memories))))
			if self.system.architecture is not None
			else "<i>(Unknown)</i>")
		row += 1
		
		table.attach(gtk.HSeparator(), 1,3, row,row+1,
		             xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL,
		             ypadding = 3)
		row += 1
		
		self.table_add_row(table, row, "CPU Type:",    "%02X"%self.system.cpu_type)
		row += 1
		self.table_add_row(table, row, "CPU Subtype:", "%04X"%self.system.cpu_subtype)
		row += 1
	
	
	def _add_register_info_page(self):
		"""
		Adds a page to the notebook showing a the registers in the system.
		"""
		# Don't add the page if there is nothing to show in it
		if (self.system.architecture is not None
		    and len(self.system.architecture.register_banks) > 0):
			label = gtk.Label("Register Banks")
			notebook = gtk.Notebook()
			notebook.set_border_width(5)
			notebook.set_tab_pos(gtk.POS_LEFT)
			self.notebook.append_page(notebook, label)
			
			for register_bank in self.system.architecture.register_banks:
				# Put a page in a notebook for each register bank
				page_label = gtk.Label(register_bank.name)
				vbox = gtk.VBox(spacing = 5)
				vbox.set_border_width(5)
				notebook.append_page(vbox, page_label)
				
				# Add a title of the register names
				title_label = gtk.Label("Other Names: %s"%(", ".join(register_bank.names)))
				title_label.set_alignment(0, 0.5)
				vbox.pack_start(title_label, fill = True, expand = False)
				
				# Table of (Names, Width, Fields, Address)
				reg_list = gtk.ListStore(str, str, str, str)
				for register in register_bank.registers:
					fields = []
					# Format the bit-field description as a list of fields
					if register.bit_field is not None:
						for name, ranges in zip(register.bit_field.field_names,
						                        register.bit_field.field_ranges):
							range_strings = ["%d:%d"%(r[0]-1, r[1])
							                 if len(r) == 2 else str(r[0])
							                 for r in ranges]
							fields.append("%s(%s)"%(name, ", ".join(range_strings)))
					
					# Add the register to the list
					reg_list.append((", ".join(register.names),
					                 "%d bit%s"%(register.width_bits,
					                             "" if register.width_bits == 1 else "s"),
					                 ", ".join(fields),
					                 "%d"%register.addr))
				
				# Create the TreeView to display the table
				treeview = gtk.TreeView(reg_list)
				scroller = gtk.ScrolledWindow()
				scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
				scroller.add(treeview)
				vbox.pack_start(scroller, fill = True, expand = True)
				cell_renderer = gtk.CellRendererText()
				
				column = gtk.TreeViewColumn("Number")
				column.pack_start(cell_renderer)
				column.add_attribute(cell_renderer, "text", 3)
				treeview.append_column(column)
				
				column = gtk.TreeViewColumn("Names")
				column.pack_start(cell_renderer)
				column.add_attribute(cell_renderer, "text", 0)
				treeview.append_column(column)
				
				column = gtk.TreeViewColumn("Width")
				column.pack_start(cell_renderer)
				column.add_attribute(cell_renderer, "text", 1)
				treeview.append_column(column)
				
				column = gtk.TreeViewColumn("Fields")
				column.pack_start(cell_renderer)
				column.add_attribute(cell_renderer, "text", 2)
				treeview.append_column(column)
	
	
	def _add_memory_info_page(self, memory):
		"""
		Adds a page to the notebook showing the system's basic info.
		"""
		
		label = gtk.Label(memory.name)
		num_rows = 9
		table = gtk.Table(rows = num_rows, columns = 3)
		table.set_border_width(5)
		table.set_col_spacing(1, 10)
		table.set_row_spacings(3)
		self.notebook.append_page(table, label)
		
		row = 0
		self.table_add_row(table, row, "Other Names:", ", ".join(memory.names))
		row += 1
		self.table_add_row(table, row, "Number:", str(memory.index))
		row += 1
		self.table_add_row(table, row, "Address Width:", "%d bits"%(memory.addr_width_bits))
		row += 1
		self.table_add_row(table, row, "Block Size:", "%d bits"%(memory.word_width_bits))
		row += 1
		self.table_add_row(table, row, "Blocks:", str(memory.size))
		row += 1
		self.table_add_row(table, row, "Space:", format_storage_size(memory.size*memory.word_width_bits))
		row += 1
		
		table.attach(gtk.HSeparator(), 1,3, row,row+1,
		             xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL,
		             ypadding = 3)
		row += 1
		
		self.table_add_row(table, row, "Assemblers:",
			", ".join(a.name for a in memory.assemblers))
		row += 1
		
		self.table_add_row(table, row, "Disassemblers:",
			", ".join(a.name for a in memory.disassemblers))
		row += 1
	
	
	@RunInBackground()
	def _add_periph_info_page(self):
		"""
		Adds a page to the notebook showing the peripherals in the system.
		"""
		# Request peripherals from the system
		periph_ids = self.system.get_peripheral_ids()
		
		# Display them in the GUI thread
		yield
		
		# Don't add if there aren't any peripherals
		if len(periph_ids) == 0:
			return
		
		# Table of (Name, Type, Subtype, Number, Supported)
		periph_list = gtk.ListStore(str, str, str, str, str)
		for periph_num, (periph_id, periph_sub_id) in enumerate(periph_ids):
			name, PeriphWidget = get_peripheral_view(periph_id, periph_sub_id)
			
			# Add the peripheral to the list
			periph_list.append((name or "Unknown",
			                    "%02X"%periph_id,
			                    "%04X"%periph_sub_id,
			                    str(periph_num),
			                    "No" if PeriphWidget is None else "Yes"))
		
		# Create the TreeView to display the table
		treeview = gtk.TreeView(periph_list)
		scroller = gtk.ScrolledWindow()
		scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		scroller.add(treeview)
		cell_renderer = gtk.CellRendererText()
		
		# Add the tab and make sure its visible as this is happening late
		label = gtk.Label("Peripherals")
		self.notebook.append_page(scroller, label)
		self.show_all()
		
		column = gtk.TreeViewColumn("Number")
		column.pack_start(cell_renderer)
		column.add_attribute(cell_renderer, "text", 3)
		treeview.append_column(column)
		
		column = gtk.TreeViewColumn("Type")
		column.pack_start(cell_renderer)
		column.add_attribute(cell_renderer, "text", 0)
		treeview.append_column(column)
		
		column = gtk.TreeViewColumn("ID")
		column.pack_start(cell_renderer)
		column.add_attribute(cell_renderer, "text", 1)
		treeview.append_column(column)
		
		column = gtk.TreeViewColumn("Sub ID")
		column.pack_start(cell_renderer)
		column.add_attribute(cell_renderer, "text", 2)
		treeview.append_column(column)
		
		column = gtk.TreeViewColumn("Supported")
		column.pack_start(cell_renderer)
		column.add_attribute(cell_renderer, "text", 4)
		treeview.append_column(column)
	
	
	def architecture_changed(self):
		"""
		Called when the architecture changes, deals with all the
		architecture-specific changes which need to be made to the GUI.
		"""
		# Create a new notebook at the top of the window
		self.remove(self.notebook)
		self.notebook.destroy()
		self.notebook = gtk.Notebook()
		self.pack_start(self.notebook, fill = True, expand = True)
		self.reorder_child(self.notebook, 0)
		
		self._add_basic_info_page()
		self._add_register_info_page()
		
		if self.system.architecture is not None:
			for memory in self.system.architecture.memories:
				self._add_memory_info_page(memory)
		
		self._add_periph_info_page()
		
		self.refresh()


