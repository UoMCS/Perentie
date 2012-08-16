#!/usr/bin/env python

"""
A GTK+ widget which can be used to fill space where a widget is unavailable, for
example if a system doesn't have a memory, this can be shown in its place in a
memory window.
"""


import gtk, gobject


class Placeholder(gtk.Alignment):
	
	def __init__(self, title, body = None, stock_icon_id = gtk.STOCK_DIALOG_INFO):
		"""
		Draws an icon, large title and some body text centered in the widget.
		"""
		gtk.Alignment.__init__(self, 0.5, 0.5)
		
		self.title         = title
		self.body          = body or ""
		self.stock_icon_id = stock_icon_id
		
		self.vbox = gtk.VBox(spacing = 15)
		self.vbox.set_border_width(15)
		self.add(self.vbox)
		
		self.icon = gtk.Image()
		self.icon.set_from_stock(self.stock_icon_id, gtk.ICON_SIZE_DIALOG)
		self.vbox.pack_start(self.icon, fill = True, expand = False)
		
		self.title_label = gtk.Label()
		self.title_label.set_markup("<span weight = 'bold' size='x-large'>%s</span>"%self.title)
		self.vbox.pack_start(self.title_label, fill = True, expand = False)
		
		self.body_label = gtk.Label()
		self.body_label.set_markup(self.body)
		self.body_label.set_line_wrap(True)
		self.vbox.pack_start(self.body_label, fill = True, expand = False)
		
		self.vbox.show_all()
