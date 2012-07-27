#!/usr/bin/env python

"""
Memory parameter container.
"""

class Memory(object):
	
	def __init__(self, index, names, addr_width_bits, word_width_bits, disassemblers = None, size = None):
		"""
		A memory in a system.
		
		index is the unique index the memory is identified by
		
		names is a list of names which may refer to this memory (the first is used
		as the default for display/output).
		
		addr_width_bits is the width of the address bus in bits.
		
		word_width_bits is the width of a memory word in bits.
		
		disassemblers is a list of Disassembler objects which are available for use
		with this memory. The first is assumed to be the default disassembler.
		Defaults to an empty list.
		
		size is the size of the memory in words. Defaults to the maximum addressable
		ammount.
		"""
		self.index           = index
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


