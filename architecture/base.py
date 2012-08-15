#!/usr/bin/env python

"""
Definition of a system which can be debugged. This class should be inherited and
fleshed-out by any CPU architecture that is desired.
"""


class Architecture(object):
	
	def __init__(self, cpu_type, cpu_subtype):
		"""
		A base-implementation of the system.
		"""
		
		# The name of the system's architecture (e.g. 'STUMP')
		self.name = None
		
		# The architecture IDs
		self.cpu_type    = cpu_type
		self.cpu_subtype = cpu_subtype
		
		# The number of bits in a "word" on this architecture
		self.word_width_bits = None
		
		# List of RegisterBanks within the system. The first register bank is
		# considered to be the "default" unless otherwise stated.
		self.register_banks = []
		
		# List of Memory objects available to the system
		self.memories = []
