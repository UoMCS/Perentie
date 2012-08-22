#!/usr/bin/env python

"""
A GTK+ widget which displays information about the connected device.
"""


import gtk, gobject

from background  import RunInBackground
from placeholder import Placeholder

from format import *


class SymbolViewer(gtk.VBox):
	
	def __init__(self, system):
		"""
		A GTK widget that displays all program symbols.
		"""
		gtk.VBox.__init__(self)
		
		self.system = system
		
		self.set_border_width(5)
		
		# The widget being displayed
		self.widget = None
		
		# Mapping from memories to treeviews
		self.treeviews = {}
		
		self.architecture_changed()
	
	
	def refresh(self):
		"""
		Refreshes information in the widget.
		"""
		# Nothing to update
		pass
	
	
	def refresh_symbols(self):
		"""
		Refreshes the list of available symbols. Call when the list changes.
		"""
		if self.system.architecture is None:
			return
		
		for memory, treeview in self.treeviews.iteritems():
			liststore = treeview.get_model()
			liststore.clear()
			symbols = self.system.image_symbols.get(memory,{})
			for symbol, (value, symbol_type) in symbols.iteritems():
				liststore.append((symbol,
				                  format_number(value, self.system.architecture.word_width_bits),
				                  symbol_type))
			treeview.columns_autosize()
	
	
	def architecture_changed(self):
		"""
		Called when the architecture changes, deals with all the
		architecture-specific changes which need to be made to the GUI.
		"""
		self.treeviews = {}
		
		# Remove the previous widget
		if self.widget:
			self.remove(self.widget)
			self.widget.destroy()
			self.widget = None
		
		# Add a new page for each memory
		if self.system.architecture is None:
			self.widget = Placeholder("Unknown Architecture",
				"The current architecture is not known and thus no "+
				"memories containing symbols can be displayed.",
				gtk.STOCK_DIALOG_WARNING)
		elif len(self.system.architecture.memories) == 0:
			self.widget = Placeholder("No Memories",
				"The current architecture does not have any memories"+
				"thus no symbols can be present.",
				gtk.STOCK_DIALOG_WARNING)
		else:
			self.widget = gtk.Notebook()
			for memory in self.system.architecture.memories:
				# Add a page with a symbol listing for each memory
				label = gtk.Label(memory.name)
				liststore = gtk.ListStore(str, str, str)
				self.treeviews[memory]  = gtk.TreeView(liststore)
				scroller = gtk.ScrolledWindow()
				scroller.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
				scroller.add(self.treeviews[memory])
				self.widget.append_page(scroller, label)
				
				cell_renderer = gtk.CellRendererText()
				
				column = gtk.TreeViewColumn("Symbol")
				column.pack_start(cell_renderer)
				column.add_attribute(cell_renderer, "text", 0)
				self.treeviews[memory].append_column(column)
				
				column = gtk.TreeViewColumn("Value")
				column.pack_start(cell_renderer)
				column.add_attribute(cell_renderer, "text", 1)
				self.treeviews[memory].append_column(column)
				
				column = gtk.TreeViewColumn("Type")
				column.pack_start(cell_renderer)
				column.add_attribute(cell_renderer, "text", 2)
				self.treeviews[memory].append_column(column)
		
		self.pack_start(self.widget, fill = True, expand=True)
		
		self.refresh_symbols()
		
		self.show_all()
		
		self.refresh()



