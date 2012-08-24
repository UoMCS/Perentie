#!/usr/bin/env python

"""
A GTK about dialog for the program. This file is where all the project meta-data
should be defined!
"""


import gtk


NAME      = "Perentie"
VERSION   = "0.1"
COPYRIGHT = "Copyright 2012, The University of Manchester"
COMMENTS  = """
A low-level debugging tool for monitoring and controlling processors and
microcontrollers.

This tool is designed to be a teaching and learning aid rather than a fully
fledged debugging platform. This tool has been written based on the ideas of the
Komodo Manchester Debugger (KMD) and aims to be backwards-compatible.
""".strip().replace("\n\n", "<br>").replace("\n", " ").replace("<br>","\n\n")
LICENSE = "GNU General Public License (GPL) Version 3"
WEBSITE = "http://cs.man.ac.uk/"
AUTHORS = [
	"Jonathan Heathcote (jdh@cs.man.ac.uk)"
]

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

