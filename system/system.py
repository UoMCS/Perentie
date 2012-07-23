#!/usr/bin/env python

"""
Definition of a system which can be debugged. This class should be inherited and
fleshed-out by any CPU architecture that is desired.
"""


class System(object):
	
	def __init__(self):
		"""
		A base-implementation of the system.
		"""
		
		# The name of the system's architecture (e.g. 'STUMP')
		self.name = None
		
		# List of RegisterBanks within the system
		self.register_banks = []
		
		# List of memories available to the system
		self.memories = []
		
		# List of peripherals supported by the system
		self.peripherals = []
