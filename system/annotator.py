#!/usr/bin/env python

"""
A set of memory annotation functions provided as a mixin for the System.

TODO: Other types of annotations for breakpoints and watchpoints.
"""

class AnnotatorMixin(object):
	"""
	Memory annotation mixin
	"""
	
	
	def __init__(self):
		pass
	
	
	def get_register_pointers(self, memory):
		"""
		Get all registers with pointers into the specified memory resulting from
		registers.
		
		Returns a list of (RegisterBank, Register) tuples.
		"""
		
		out = []
		for register_bank in self.architecture.register_banks:
			for register in register_bank.registers:
				if register.pointer is not None and memory in register.pointer.memories:
					out.append((register_bank, register))
		
		return out
	
	
	def get_symbol_pointers(self, memory):
		"""
		Get all registers with pointers into the specified memory resulting from
		registers.
		
		Returns a list of (symbol_name, value) tuples
		"""
		
		out = []
		for symbol_name, (value, symbol_type) in self.image_symbols.get(memory,{}).iteritems():
			# Do something different for each type...
			out.append((symbol_name, value))
		return out
