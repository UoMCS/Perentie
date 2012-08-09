#!/usr/bin/env python

"""
Peripheral widgets for xilinx devices.
"""

from os.path   import dirname, join
from threading import Lock

from ..background       import RunInBackground
from ..progress_monitor import ProgressMonitor

import gtk

from base import PeripheralWidget

def read_bitfile(f):
	"""
	Given a file-object containing a Xilinx FPGA bitfile, return:
	(design_name, device_name, (datestamp, timestamp), data)
	
	This implementation is based on the fpga_load utility. It contains various
	unexplained behaviours which just happen to work... Sorry about that.
	"""
	
	# Discard
	f.read(1)
	
	# Discard
	offset_to_name = ord(f.read(1))
	f.read(offset_to_name+4)
	
	# Design name
	design_name_length = ord(f.read(1))
	design_name = f.read(design_name_length).strip("\x00")
	
	# Discard
	f.read(2)
	
	# Device name
	device_name_length = ord(f.read(1))
	device_name = f.read(device_name_length).strip("\x00")
	
	# Discard
	f.read(2)
	
	# Date-stamp
	datestamp_length = ord(f.read(1))
	datestamp = f.read(datestamp_length).strip("\x00")
	
	# Discard
	f.read(2)
	
	# Time-stamp
	timestamp_length = ord(f.read(1))
	timestamp = f.read(timestamp_length).strip("\x00")
	
	# Discard
	f.read(1)
	
	# Length of the bit-file data (the real meat of the problem)
	data_length = 0
	for byte in f.read(4):
		data_length = (data_length << 8) | ord(byte)
	
	data = f.read(data_length)
	
	return (design_name, device_name, (datestamp, timestamp), data)



class Spartan3(gtk.Table, PeripheralWidget):
	"""
	A widget for controlling an attached spartan-3 FPGA.
	"""
	
	# Filenames of icons of various sizes for the widget
	ICON_FILENAMES = {
		48 : join(dirname(__file__), "icons", "fpga_48.png"),
		24 : join(dirname(__file__), "icons", "fpga_24.png"),
		22 : join(dirname(__file__), "icons", "fpga_22.png"),
		16 : join(dirname(__file__), "icons", "fpga_16.png"),
	}
	
	# Mapping of the major part of the sub_id to a model name (longname,
	# shortname)
	MODEL_MAJOR = {
		0x00: ("XC3S50",  "3s50"),
		0x02: ("XC3S200", "3s200"),
		0x04: ("XC3S400", "3s400"),
		0x0A: ("XC3S1000","3s1000"),
		0x0F: ("XC3S1500","3s1500"),
		0x14: ("XC3S2000","3s2000"),
		0x28: ("XC3S4000","3s4000"),
		0x32: ("XC3S5000","3s5000"),
	}
	
	# Mapping of the minor part of the sub_id to a model name (longname,
	# shortname)
	MODEL_MINOR = {
		0x00: ("-PC84",  "pc84"),
		0x01: ("-VQ100", "vq100"),
		0x02: ("-CS144", "cs144"),
		0x03: ("-TQ144", "tq144"),
		0x04: ("-PQ208", "pq208"),
		0x05: ("-PQ240", "pq240"),
		0x06: ("-HQ240", "hq240"),
		0x07: ("-BG256", "bg256"),
		0x08: ("-FG256", "fg256"),
		0x09: ("-CS280", "cs280"),
		0x0A: ("-BG352", "bg352"),
		0x0B: ("-BG432", "bg432"),
		0x0C: ("-FG456", "fg456"),
		0x0D: ("-BG560", "bg560"),
		0x0E: ("-FG676", "fg676"),
		0x0F: ("-FG680", "fg680"),
		0x10: ("-CP132", "cp132"),
		0x11: ("-FT256", "ft256"),
		0x12: ("-FG900", "fg900"),
		0x13: ("-FG1156","fg1156"),
	}
	
	
	def __init__(self, system, periph_num, periph_id, periph_sub_id):
		gtk.Table.__init__(self, rows = 6, columns = 2, homogeneous = False)
		PeripheralWidget.__init__(self, system, periph_num, periph_id, periph_sub_id)
		
		# Lock for bit-file data variables access
		self.data_lock   = Lock()
		self.design_name = None
		self.device_name = None
		self.datestamp   = None
		self.timestamp   = None
		self.data        = None
		
		# Space the widget's contents from the edge of the container as they're just
		# buttons and labels (which don't have their own padding).
		self.set_border_width(5)
		
		# Space between labels and entries
		self.set_col_spacing(0, 10)
		
		# File name selection box/button
		self.filename_box   = gtk.FileChooserButton("Select a Bit File")
		
		# Set filename filters
		bit_file_filter = gtk.FileFilter()
		bit_file_filter.set_name("FPGA Bit File (*.bit)")
		bit_file_filter.add_pattern("*.bit")
		self.filename_box.add_filter(bit_file_filter)
		
		all_files_filter = gtk.FileFilter()
		all_files_filter.set_name("All Files")
		all_files_filter.add_pattern("*")
		self.filename_box.add_filter(all_files_filter)
		
		self.filename_box.connect("file-set", self._on_file_set)
		
		self._add_row("Bit File:", self.filename_box, 0)
		
		# Space between file-chooser and meta-data
		self.set_row_spacing(0, 5)
		
		# Show the design meta-data
		self.design_name_label     = gtk.Label()
		self.device_name_label     = gtk.Label()
		self.date_time_stamp_label = gtk.Label()
		
		self._add_row("Design Name:",   self.design_name_label,     1)
		self._add_row("Target Device:", self.device_name_label,     2)
		self._add_row("Compile time:",  self.date_time_stamp_label, 3)
		
		# Space before progress viewer
		self.set_row_spacing(3, 5)
		
		# Add a progress monitor
		self.progress_monitor = ProgressMonitor(self.system, auto_hide = False)
		self.progress_monitor.add_adjustment(Spartan3.downloader_decorator.get_adjustment(self))
		self._add_row("Download Progress:", self.progress_monitor, 4)
		
		# Space before button
		self.set_row_spacing(4, 5)
		
		# Add a download button
		self.download_btn = gtk.Button("Download onto FPGA")
		self.download_btn.set_sensitive(False)
		self.download_btn.connect("clicked", self._on_donwload_clicked)
		self.attach(self.download_btn, 1,2, 5,6,
		            xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.FILL)
	
	
	def _add_row(self, label, widget, row):
		"""
		Add a row to the table containing a label with the text provieded in label
		and a widget named widget in the given row.
		"""
		label_widget = gtk.Label(label)
		
		self.attach(label_widget, 0, 1, row, row+1,
		            xoptions=gtk.FILL, yoptions=gtk.FILL)
		self.attach(widget, 1, 2, row, row+1,
		            xoptions=gtk.EXPAND|gtk.FILL, yoptions=gtk.FILL)
		
	
	
	def get_icon(self, size):
		width, height = gtk.icon_size_lookup(size)
		
		suitable_icons = dict(filter((lambda (s,f): s >= width),
		                             Spartan3.ICON_FILENAMES.iteritems()))
		if suitable_icons:
			# If we have big enough icons, pick the smallest (i.e. closest to
			# requested size)
			icon_filename = suitable_icons[min(suitable_icons)]
		else:
			# If don't have big enough icons, pick the largest available
			icon_filename = Spartan3.ICON_FILENAMES[max(Spartan3.ICON_FILENAMES)]
		
		pixbuf = gtk.gdk.pixbuf_new_from_file_at_size(icon_filename, width, height)
		
		return pixbuf
	
	
	def get_model(self, short_version = False):
		sub_id0 = (self.periph_sub_id>>8) & 0xFF
		sub_id1 = (self.periph_sub_id>>0) & 0xFF
		
		major = Spartan3.MODEL_MAJOR.get(sub_id0, "???")
		minor = Spartan3.MODEL_MINOR.get(sub_id1, "???")
		
		return "%s%s"%(major[short_version],minor[short_version])

	
	def get_name(self):
		
		return "Xilinx Spartan-3 %s FPGA"%(self.get_model())
	
	
	def get_short_name(self):
		return "FPGA"
	
	
	def get_progress_adjustments(self):
		return (
			PeripheralWidget.get_progress_adjustments(self)
			+ [(Spartan3.downloader_decorator.get_adjustment(self), "FPGA Download")]
		)
	
	
	@RunInBackground(start_in_gtk = True)
	def _on_file_set(self, filename_box):
		# Get the filename
		filename = self.filename_box.get_filename()
		
		# Do file loading in a background thread
		yield
		
		# Try and open the file
		f = None
		if filename is not None:
			try:
				f = open(filename, "rb")
			except Exception, e:
				# Log the error
				self.system.log(e, True)
		
		# Try and load the file
		with self.data_lock:
			self.design_name = None
			self.device_name = None
			self.datestamp   = None
			self.timestamp   = None
			self.data        = None
			
			if f is not None:
				# Try to open the design
				try:
					(
						self.design_name,
						self.device_name,
						(self.datestamp, self.timestamp),
						self.data,
					) = read_bitfile(f)
				except Exception, e:
					self.system.log(e, True)
		
		# Display the file's meta-data in the GTK thread.
		yield
		
		design_name_text = self.design_name or ""
		
		if self.device_name is not None:
			if self.device_name == self.get_model(short_version = True):
				device_name_text = self.device_name
			else:
				device_name_text = "%s (Warning: Different Model!)"%self.device_name
		else:
			device_name_text = ""
		
		if self.datestamp is not None and self.timestamp is not None:
			timestamp_text = "%s %s"%(self.datestamp, self.timestamp)
		else:
			timestamp_text = ""
		
		# Update meta-data labels
		self.design_name_label.set_text(design_name_text)
		self.device_name_label.set_text(device_name_text)
		self.date_time_stamp_label.set_text(timestamp_text)
		
		# Enable download button if there's data
		self.download_btn.set_sensitive(self.data is not None)
	
	
	
	downloader_decorator = RunInBackground(start_in_gtk = True)
	@downloader_decorator
	def _on_donwload_clicked(self, download_btn):
		# Disable the download button (makes it obvious the system is doing
		# something)
		self.download_btn.set_sensitive(False)
		self.download_btn.set_label("Downloading...")
		
		# Run the downloader in the background
		yield
		
		with self.data_lock:
			data_length = len(self.data)
			
			try:
				for progress in self.system.peripheral_download(self.periph_num, self.data):
					# Report progress
					yield (progress, data_length)
			except Exception, e:
				# Something bad happened and the download failed.
				self.system.log(e, True)
		
		# Return to the GTK thread to re-enable the download button
		yield
		
		self.download_btn.set_sensitive(True)
		self.download_btn.set_label("Download onto FPGA")
