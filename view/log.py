#!/usr/bin/env python

"""
A GTK+ widget for displaying the system log.
"""


import gtk, gobject, glib


class LogViewer(gtk.ScrolledWindow):
	
	__gsignals__ = {
		# Emitted when a new entry appears (argument is whether the flag was set)
		'update': (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (bool,)),
	}
	
	# The time (sec) a new log entry is highlighted
	HIGHLIGHT_TIMEOUT = 2
	
	def __init__(self, system):
		"""
		A simple log viewer as a table.
		"""
		gtk.ScrolledWindow.__init__(self)
		
		self.system = system
		
		self.system.on_log(self._on_log, False)
		
		
		# List store of text, bold, colour, tooltip
		self.list_store = gtk.ListStore(str, int, str, str)
		self.tree_view = gtk.TreeView(self.list_store)
		
		cell_renderer = gtk.CellRendererText()
		cell_renderer.set_property("editable", False)
		
		col = gtk.TreeViewColumn("Log")
		col.pack_start(cell_renderer)
		col.add_attribute(cell_renderer, "text", 0)
		col.add_attribute(cell_renderer, "weight", 1)
		col.add_attribute(cell_renderer, "foreground", 2)
		self.tree_view.append_column(col)
		
		# Only one column
		self.tree_view.set_headers_visible(False)
		
		self.tree_view.set_tooltip_column(3)
		
		# Show scrollbars if needed
		self.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
		self.add(self.tree_view)
		self.tree_view.show()
	
	
	def _on_log(self, exception, traceback, flag, in_gtk_thread):
		if not in_gtk_thread:
			glib.idle_add(self._on_log, exception, traceback, flag, True)
		else:
			colour = "#FF0000" if flag else "#000000"
			it = self.list_store.append((str(exception),   # Simple description
			                             800,              # Initially bold
			                             colour,           # Colour
			                             glib.markup_escape_text(traceback))) # Full description
			
			# Scroll into view
			self.tree_view.scroll_to_cell(len(self.list_store) - 1)
			
			self.emit("update", flag)
			
			# Remove highlight after a few seconds
			def remove_highlight():
				self.list_store.set_value(it, 1, 400)
				return False
			glib.timeout_add_seconds(LogViewer.HIGHLIGHT_TIMEOUT, remove_highlight)
