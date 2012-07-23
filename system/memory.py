#!/usr/bin/env python

"""
Memory parameter container.
"""

class Memory(object):
	
	def __init__(self, names, addr_width_bits, word_width_bits, disassemblers = None, size = None):
		"""
		A memory in a system.
		
		names is a list of names which may refer to this memory (the first is used
		as the default for display/output).
		
		addr_width_bits is the width of the address bus in bits. Up to 32-bits
		allowed due to limitations in the backend (see Protocol._memory_write).
		
		word_width_bits is the width of a memory word in bits. Due to limitations in the
		backend (see Protocol._memory_write) this must be no more than 64 and
		accesses will be rounded up to either 8, 16, 32 or 64.
		
		disassemblers is a list of Disassembler objects which are available for use
		with this memory. The first is assumed to be the default disassembler.
		Defaults to an empty list.
		
		size is the size of the memory in words. Defaults to the maximum addressable
		ammount.
		"""
		self.names           = names
		self.addr_width_bits = addr_width_bits
		self.word_width_bits = word_width_bits
		self.disassemblers   = disassemblers or []
		self.size            = size or (1<<addr_width_bits)
	
	
	@property
	def name(self):
		"""
		An alias for the default name.
		"""
		return self.names[0]


