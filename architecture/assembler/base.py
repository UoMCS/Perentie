#!/usr/bin/env python

"""
The interface expected for assemblers.
"""


class Assembler(object):
	
	def __init__(self):
		# A name for the Assembler's language
		self.name = None
	
	
	def assemble(self, input_filename):
		"""
		Assemble the provided input file and return the output memory image filename.
		"""
		raise NotImplementedError("Assembler not implemented!")
	
	
	def assemble_instruction(self, instruction, length, addr, symbols = None):
		"""
		Assemble the provided single instruction into a value of size length.
		Symbols should be a dictionary of symbols to addresses. Return the
		instruction as an int.
		"""
		raise NotImplementedError("Instruction Assembler not implemented!")
