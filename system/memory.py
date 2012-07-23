#!/usr/bin/env python

"""
Memory parameter container.
"""

class Memory(object):
	
	def __init__(self, names, addr_width, word_width, disassemblers = None, size = None):
		"""
		A memory in a system.
		
		names is a list of names which may refer to this memory (the first is used
		as the default for display/output).
		
		addr_width is the width of the address bus in bytes, up to 4-bytes due to
		limitations in the backend (see Protocol._memory_write).
		
		word_width is the width of a memory word in bytes. Due to limitations in the
		backend (see Protocol._memory_write) this must be either 1, 2, 4 or 8.
		
		disassemblers is a list of Disassembler objects which are available for use
		with this memory. The first is assumed to be the default disassembler.
		Defaults to an empty list.
		
		size is the size of the memory in words. Defaults to the maximum addressable
		ammount.
		"""
		self.names         = names
		self.addr_width    = addr_width
		self.word_width    = word_width
		self.disassemblers = disassemblers or []
		self.size          = size or (1<<addr_width)
	
	
	@property
	def name(self):
		"""
		An alias for the default name.
		"""
		return self.names[0]


