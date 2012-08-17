#!/usr/bin/env python

"""
Peripheral widgets for xilinx devices.
"""

from os.path   import dirname, join

import gtk, pango, gobject

from base         import PeripheralWidget
from ..background import RunInBackground
from ..format     import *



class DebugController(gtk.Notebook, PeripheralWidget):
	"""
	A widget for controlling a design running on an attached FPGA.
	"""
	
	__gsignals__ = {
		# Emitted when the peripheral viewer would like the whole UI to be refreshed
		'global-refresh': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, tuple()),
	}
	
	# Filenames of icons of various sizes for the widget
	ICON_FILENAMES = {
		32 : join(dirname(__file__), "icons", "controller_32.png"),
		22 : join(dirname(__file__), "icons", "controller_22.png"),
		16 : join(dirname(__file__), "icons", "controller_16.png"),
	}
	
	
	def __init__(self, system, periph_num, periph_id, periph_sub_id):
		gtk.Notebook.__init__(self)
		PeripheralWidget.__init__(self, system, periph_num, periph_id, periph_sub_id)
		
		self.set_border_width(5)
		
		# Basic controls tab
		vbox = gtk.VBox(spacing = 5)
		label = gtk.Label("Basic")
		self.append_page(vbox, label)
		self._init_clock_gui(vbox)
		self._init_memory_gui(vbox)
		
		# Scanpath tab
		vbox = gtk.VBox()
		vbox.set_border_width(5)
		label = gtk.Label("Scan Path")
		self.append_page(vbox, label)
		self.scan_path_chooser = gtk.FileChooserButton("Select Scanpath Description")
		vbox.pack_start(self.scan_path_chooser, fill = True, expand = False)
		self.scan_path_load_btn = gtk.Button("Load Scan Path Description")
		vbox.pack_start(self.scan_path_load_btn, fill = True, expand = False)
	
	
	def _init_clock_gui(self, vbox):
		"""
		Set up the GUI for the clock control
		"""
		self.clock_frame = gtk.Frame("Clock")
		self.clock_table = gtk.Table(rows = 3, columns = 2)
		self.clock_table.set_col_spacings(10)
		self.clock_table.set_row_spacings(5)
		self.clock_table.set_border_width(5)
		self.clock_frame.add(self.clock_table)
		vbox.pack_start(self.clock_frame, fill = True, expand = False)
		
		label = gtk.Label("Instruction Cycle Count")
		label.set_alignment(0.0,0.5)
		self.clock_table.attach(label, 0,1, 0,1,
		                        xoptions = gtk.FILL, yoptions = gtk.FILL)
		self.fetch_cycles = gtk.Label("0")
		self.clock_table.attach(self.fetch_cycles, 1,2, 0,1,
		                        xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL)
		
		label = gtk.Label("Fetch Signal")
		label.set_alignment(0.0,0.5)
		self.clock_table.attach(label, 0,1, 1,2,
		                        xoptions = gtk.FILL, yoptions = gtk.FILL)
		self.fetch_signal = gtk.Label("High")
		self.clock_table.attach(self.fetch_signal, 1,2, 1,2,
		                        xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL)
		
		self.clock_btn = gtk.Button("Pulse Clock")
		self.clock_btn.connect("clicked", self._on_clock_btn_clicked)
		self.clock_table.attach(self.clock_btn, 0,2, 2,3,
		                        xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL|gtk.EXPAND)
	
	
	def _init_memory_gui(self, vbox):
		"""
		Set up the GUI for memory viewing
		"""
		self.memory_frame = gtk.Frame("Memory Interface")
		self.memory_table = gtk.Table(rows = 3, columns = 3)
		self.memory_table.set_col_spacings(10)
		self.memory_table.set_row_spacings(5)
		self.memory_table.set_border_width(5)
		self.memory_frame.add(self.memory_table)
		vbox.pack_start(self.memory_frame, fill = True, expand = False)
		
		label = gtk.Label("Address")
		label.set_alignment(0.0,0.5)
		self.memory_table.attach(label, 0,1, 0,1,
		                         xoptions = gtk.FILL, yoptions = gtk.FILL)
		self.memory_addr = gtk.Label("0x0000")
		self.memory_table.attach(self.memory_addr, 1,2, 0,1,
		                         xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL)
		
		label = gtk.Label("Data In")
		label.set_alignment(0.0,0.5)
		self.memory_table.attach(label, 0,1, 1,2,
		                         xoptions = gtk.FILL, yoptions = gtk.FILL)
		self.memory_data_in = gtk.Label("0x0000")
		self.memory_table.attach(self.memory_data_in, 1,2, 1,2,
		                         xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL)
		self.read_enable = gtk.Label()
		self.read_enable.set_alignment(0.0,0.5)
		self.read_enable.set_width_chars(15)
		self.memory_table.attach(self.read_enable, 2,3, 1,2,
		                         xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL)
		
		label = gtk.Label("Data Out")
		label.set_alignment(0.0,0.5)
		self.memory_table.attach(label, 0,1, 2,3,
		                         xoptions = gtk.FILL, yoptions = gtk.FILL)
		self.memory_data_out = gtk.Label("0x0000")
		self.memory_table.attach(self.memory_data_out, 1,2, 2,3,
		                         xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL)
		self.write_enable = gtk.Label()
		self.write_enable.set_alignment(0.0,0.5)
		self.write_enable.set_width_chars(15)
		self.memory_table.attach(self.write_enable, 2,3, 2,3,
		                         xoptions = gtk.FILL|gtk.EXPAND, yoptions = gtk.FILL)
	
	
	def get_icon(self, size):
		width, height = gtk.icon_size_lookup(size)
		
		suitable_icons = dict(filter((lambda (s,f): s >= width),
		                             DebugController.ICON_FILENAMES.iteritems()))
		if suitable_icons:
			# If we have big enough icons, pick the smallest (i.e. closest to
			# requested size)
			icon_filename = suitable_icons[min(suitable_icons)]
		else:
			# If don't have big enough icons, pick the largest available
			icon_filename = DebugController.ICON_FILENAMES[max(DebugController.ICON_FILENAMES)]
		
		pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(icon_filename, width, height)
		
		return pixbuf
	
	
	def get_name(self):
		
		return "Debug Controller"
	
	
	def get_short_name(self):
		return "Debug"
	
	
	@RunInBackground()
	def _on_clock_btn_clicked(self, btn):
		"""
		Callback on clicking the clock button. Request that the clock be toggled.
		"""
		
		# Write any old status
		self.system.periph_set_status(self.periph_num, 0)
		
		# Trigger a refresh since we may have updated the cycle count
		yield
		self.emit("global-refresh")
	
	
	@RunInBackground()
	def refresh(self):
		"""
		Refresh the status displays
		"""
		state = self.system.periph_get_status(self.periph_num)
		
		# Get the requested memory address, read data and write data (3 16-bit
		# numbers)
		mem_info = self.system.periph_get_message(self.periph_num, 2*3)
		
		# Decode into 16-bit values
		if len(mem_info) == 2*3:
			values = []
			i = iter(map(ord, mem_info))
			for lsb, msb in zip(i,i):
				values.append(lsb | (msb<<8))
		else:
			values = [0,0,0]
		
		# Update GUI in GTK thread
		yield
		
		# Clock & fetch state
		self.fetch_cycles.set_text(str(state&0xFF))
		self.fetch_signal.set_markup("<b>High</b>" if state&0x400 else "Low")
		
		# Read/write enables
		self.read_enable.set_markup("Read Enable " +
		                            ("<b>High</b>"
		                             if state&0x100
		                             else "Low"))
		self.write_enable.set_markup("Write Enable "+
		                             ("<b>High</b>"
		                              if state&0x200
		                              else "Low"))
		
		# Memory Addresses & Data
		addr, data_in, data_out = values
		self.memory_addr.set_markup("<tt>%s</tt>"%format_number(addr, 16))
		self.memory_data_in.set_markup("<tt>%s</tt>"%format_number(data_in, 16))
		self.memory_data_out.set_markup("<tt>%s</tt>"%format_number(data_out, 16))
