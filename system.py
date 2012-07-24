#!/usr/bin/env python

"""
A system which is being debugged.
"""

from architecture import get_architecture


class System(object):
	
	def __init__(self, back_end, name = None):
		"""
		A container for all the pieces related to a system.
		
		back_end is a BackEnd for the system
		
		name is a user-friendly name for display to the user when referring to this
		machine.
		"""
		
		self.back_end = back_end
		self.name     = name
		
		# Get the board's details
		((self.cpu_type, self.cpu_sub_type),
		 peripherals,
		 segments) = self.back_end.get_board_definition()
		
		# Get the board's architecture model
		self.architecture = get_architecture(self.cpu_type, self.cpu_sub_type)

