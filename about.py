#!/usr/bin/env python

"""
A GTK about dialog for the program. This file is where all the project meta-data
should be defined!
"""

NAME      = "Perentie"

# VERSION is defined by the VERSION file.

COMMENTS  = """
A simple debug monitor for processors and microcontrollers.

This tool is designed to be a teaching and learning aid rather than a fully
fledged debugging platform. This tool has been written based on the ideas of the
Komodo Manchester Debugger (KMD) and aims to be backwards-compatible.
"""

WEBSITE = "http://www.cs.manchester.ac.uk/"

AUTHORS = [
	"Jonathan Heathcote <mail@jhnet.co.uk>"
]

COPYRIGHT = "Copyright 2015, The University of Manchester"

# LICENSE is defined by the LICENSE file.

################################################################################

import os, glob

import gtk

def _path(*path_parts):
	"""
	Get the path of the given file in the root of the program.
	"""

	return os.path.join(os.path.dirname(__file__), *path_parts)


def _last_line(s):
	"""
	Get the last line of a string.
	"""
	return s.split("\n")[-1].strip()


def _reflow(s):
	"""
	Reflow a string so that all text in a paragraph (denoted by text on
	consecutive lines) is merged onto one line.
	"""
	return s.strip().replace("\n\n", "<br>").replace("\n", " ").replace("<br>","\n\n")


################################################################################

# Defined in version file
VERSION   = _last_line(open(_path("VERSION"),"r").read().strip())

# Include from file.
LICENSE = open(_path("LICENSE"),"r").read()

# Load from icon file
ICON = gtk.gdk.pixbuf_new_from_file(_path("logo", "icon_64.png"))

################################################################################

class AboutDialog(gtk.AboutDialog):

	def __init__(self):

		gtk.AboutDialog.__init__(self)

		self.set_name(NAME)
		self.set_version(VERSION)
		self.set_copyright(COPYRIGHT)
		self.set_comments(_reflow(COMMENTS))
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
