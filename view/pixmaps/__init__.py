#!/usr/bin/env python

"""
Loads and provides access to various pixmaps
"""

import os

import gtk


def load_pixmap(name):
	return gtk.gdk.pixbuf_new_from_file(os.path.join(os.path.dirname(__file__), name))


# Icons for pointers in memory viewers
POINTER_DEFAULT    = load_pixmap("default.png")
POINTER_REGISTER   = load_pixmap("register.png")
POINTER_PC         = load_pixmap("PC.png")
POINTER_LR         = load_pixmap("LR.png")
POINTER_SP         = load_pixmap("SP.png")
POINTER_SP         = load_pixmap("SP.png")
POINTER_BREAKPOINT = load_pixmap("breakpoint.png")
POINTER_WATCHPOINT = load_pixmap("watchpoint.png")
POINTER_SYMBOL     = load_pixmap("symbol.png")
