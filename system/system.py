#!/usr/bin/env python

"""
Top-level of the system.
"""


class System(object):
	
	def __init__(self, backend):
		"""
		A base-implementation of the system. Takes a back-end to communicate with
		the actual system.
		"""
		
		# The back-end with which the system communicates with the world
		self.backend = backend
		
		# The name of the system's architecture (e.g. 'STUMP')
		self.name = None
		
		# List of RegisterBanks within the system
		self.register_banks = []
		
		# List of memories available to the system
		self.memories = []
		
		# List of peripherals supported by the system
		self.peripherals = []
