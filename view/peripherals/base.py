#!/usr/bin/env python

"""
The base class upon which peripheral viewing widgets should be built.

Each class should also implement the global-refresh signal (with no arguments)!
"""

class PeripheralWidget(object):
	
	# Note:
	# Each class should also implement the global-refresh signal (with no
	# arguments)!
	
	def __init__(self, system, periph_num, periph_id, periph_sub_id):
		"""
		Takes a refrence to the system being debugged and the id and sub_id of the
		peripheral to be viewed. periph_num is the index of the device in the
		peripheral list.
		"""
		self.system        = system
		self.periph_num    = periph_num
		self.periph_id     = periph_id
		self.periph_sub_id = periph_sub_id
	
	
	def get_icon(self, size):
		"""
		Get a gtk.Image at the requested size which will serve as an icon for the
		peripheral.
		"""
		raise NotImplementedError()
	
	
	def get_name(self):
		"""
		Get a name which fully describes the peripheral.
		"""
		raise NotImplementedError()
	
	
	def get_short_name(self):
		"""
		Get a short name for toolbar buttons etc.
		"""
		raise NotImplementedError()
	
	
	def get_progress_adjustments(self):
		"""
		Return a list of (adjustment, name) tuples for any background jobs which may
		want their progress displayed.
		"""
		return []
	
	
	def refresh(self):
		"""
		Called whenever the widget should refresh its contents.
		"""
		pass
	
	
	def architecture_changed(self, periph_num):
		"""
		Called whenever the system's architecture has changed. The peripheral number
		within the new architecture is also given.
		
		Note that the widget is destroyed if the architecture changes to one which
		has a different type/subtype.
		"""
		self.periph_num = periph_num
