#!/usr/bin/env python

"""
An object which deals with presenting memory annotations

TODO: Other types of annotations for breakpoints and watchpoints.
"""

from pixmaps import *
from format  import *


class Annotation(object):
	
	def __init__(self, system, memory, addr):
		"""
		An base object which deals with presenting memory annotations. Takes the
		address the annotation is pointing at.
		"""
		self.system = system
		self.memory = memory
		self.addr   = addr
	
	
	def get_pointer_pixbuf(self):
		"""
		Get an icon for displaying in the memory listing.
		"""
		return POINTER_DEFAULT
	
	
	def get_tooltip(self):
		"""
		Generate some tooltip text describing the annotation.
		"""
		return ""
	
	
	def get_colour(self):
		"""
		Get the colour to use when displaying an address with this pointer
		"""
		return "#000000"
	
	
	def get_priority(self):
		"""
		The priority assigned to displaying this pointer
		"""
		return 0


class RegisterAnnotation(Annotation):
	
	def __init__(self, system, memory, addr, register_bank, register):
		Annotation.__init__(self, system, memory, addr)
		
		self.register_bank = register_bank
		self.register      = register
	
	
	def get_pointer_pixbuf(self):
		return {
			"PC": POINTER_PC,
			"LR": POINTER_LR,
			"SP": POINTER_SP,
		}.get(self.register.pointer.category, POINTER_REGISTER)
	
	
	def get_colour(self):
		return {
			"PC": "#4E9A06",
			"LR": "#9A6B06",
			"SP": "#065A9A",
		}.get(self.register.pointer.category, "#000000")
	
	
	def get_priority(self):
		# In order of ascending priority...
		priorities = ["LR", "SP", "PC"]
		
		if self.register.pointer.category in priorities:
			return 10 + priorities.index(self.register.pointer.category)
		else:
			return 0
	
	
	def get_tooltip(self):
		return "%s.%s == <tt>%s</tt>"%(self.register_bank.name,
		                      self.register.name,
		                      format_number(self.addr, self.memory.word_width_bits))

