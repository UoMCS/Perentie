#!/usr/bin/env python

"""
The interface expected for disassemblers.
"""


class Disassembler(object):
	
	def __init__(self):
		# A name for the disassembler's language
		self.name = None
	
	
	def disassemble(self, memory_read, program_start_addr, start_addr, num_instrs):
		"""
		Given the starting address of a program, disassemble num_instrs starting
		from start_addr as found in memory_read. Should return a list of
		num_instrs tuples (addr, num_instr_bits, instr_bits, instr_asm).
		
		The memory interface should be a callable:
		memory_read(addr, num_words) -> [int, ...]
		"""
		raise NotImplementedError("Disassembler not implemented!")
	
	
	def disassemble(self, memory_read, program_start_addr, start_addr, num_instrs):
		"""
		Given the starting address of a program, disassemble num_instrs starting
		from start_addr as found in memory_read. Should return a list of
		num_instrs tuples (addr, num_instr_bits, instr_bits, instr_asm).
		
		The memory interface should be a callable:
		memory_read(addr, num_words) -> [int, ...]
		"""
		raise NotImplementedError("Disassembler not implemented!")
	
	
	def assemble_instruction(self, instruction, length, addr, symbols = None):
		"""
		Reassemble the provided single instruction into a value of size length.
		Symbols should be a dictionary of symbols to addresses. Return the
		instruction as an int.
		"""
		raise NotImplementedError("Instruction Assembler not implemented!")
