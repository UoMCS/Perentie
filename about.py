#!/usr/bin/env python

"""
A GTK about dialog for the program. This file is where all the project meta-data
should be defined!
"""

import os, glob

import gtk


NAME      = "Perentie"
VERSION   = "0.1"
COPYRIGHT = "Copyright 2012, The University of Manchester"
COMMENTS  = """
A simple debug monitor for processors and microcontrollers.

This tool is designed to be a teaching and learning aid rather than a fully
fledged debugging platform. This tool has been written based on the ideas of the
Komodo Manchester Debugger (KMD) and aims to be backwards-compatible.
""".strip().replace("\n\n", "<br>").replace("\n", " ").replace("<br>","\n\n")
LICENSE = "GNU General Public License (GPL) Version 3"
WEBSITE = "http://cs.man.ac.uk/"
AUTHORS = [
	"Jonathan Heathcote (jdh@cs.man.ac.uk)"
]
ICON = gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.dirname(__file__), "logo", "icon_64.png"))

class AboutDialog(gtk.AboutDialog):
	
	def __init__(self):
		
		gtk.AboutDialog.__init__(self)
		
		self.set_name(NAME)
		self.set_version(VERSION)
		self.set_copyright(COPYRIGHT)
		self.set_comments(COMMENTS)
		self.set_license(LICENSE)
		self.set_website(WEBSITE)
		self.set_authors(AUTHORS)
		self.set_logo(ICON)


def get_icon_list():
	"""
	Returns a list of pixbufs each containing different sizes of the icon for use
	by window.set_icon_list.
	"""
	icons = []
	
	icon_paths = glob.glob(os.path.join(os.path.dirname(__file__), "logo", "icon_*.png"))
	for icon_path in icon_paths:
		icons.append(gtk.gdk.pixbuf_new_from_file(icon_path))
	
	return icons

