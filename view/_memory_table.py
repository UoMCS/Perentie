#!/usr/bin/env python

"""
A model-style object which deals with fetching and presenting user data without
fiddling around with messy GTK details.
"""

from format import *


class MemoryTable(object):
	
	def __init__(self, system, memory, align = True):
		"""
		A base-object which fetches and loads data from the memory for populating a
		listing on screen.
		
		system is the system to which the memory is attached
		
		memory is the memory block which is to be requested
		
		align indicates whether displayed rows can be aligned to a sensible address
		(True) or whether rows should start from the requested address exactly
		(False)
		"""
		self.system = system
		self.memory = memory
		self.align  = align
	
	
	def mask_addr(self, addr):
		return addr & ((1<<self.memory.addr_width_bits) - 1)
	
	
	def set_align(self, align):
		self.align = align
	def get_align(self):
		return self.align
	
	
	def get_columns(self):
		"""
		Return a list of extra columns this table has
		"""
		raise NotImplementedError()
	
	
	def set_cell(self, addr, row, column, new_data):
		"""
		Request the setting of a new value of a specific cell in the last output
		get_data returned for that address.
		
		XXX: This interface is a horrible idea, try and clean it up.
		"""
		raise NotImplementedError()
	
	
	def get_data(self, addr, num_rows):
		"""
		Returns num_rows tuples (addr, length, cols) where:
		
		addr is the address which the row represents. The first row may not be the
		one requested if, for example, a disassembler wishes to snap to an
		instruction bounry.
		
		length is the length in memory words that this row contains
		
		cols is a list of additional columns of data corresponding to the column
		names returned by get_columns().
		"""
		raise NotImplementedError()



class MemoryWordTable(MemoryTable):
	
	def __init__(self, system, memory, num_words = 1, num_elems = 1, align = True):
		"""
		A MemoryTable which simply fetches blocks of the given number of memory
		words with no additional data.
		
		num_words is the number of words per element (elements are displayed as a
		single, little-endian number)
		
		num_elems is the number of elements per row
		
		align indicates whether displayed rows should be aligned (True) or whether
		rows should start from the requested address exactly (False)
		"""
		MemoryTable.__init__(self, system, memory, align)
		
		self.num_words = num_words
		self.num_elems = num_elems
		
		self.element_size = self.num_words * self.memory.word_width_bits
	
	
	def get_columns(self):
		return ["Data"]*self.num_elems + ["ASCII"]
	
	
	def set_cell(self, addr, row, column, new_data):
		if column < self.num_elems:
			# Calculate address the cell represents
			addr += self.mask_addr((row * self.num_elems) + column) * self.num_words
			
			try:
				# Try and write the new value
				value = self.system.evaluate(new_data)
				self.system.write_memory(self.memory, self.num_words, addr, [value])
			except Exception, e:
				# The user entered something invalid, ignore the edit
				self.system.log(e, True)
		
		else:
			# Do nothing if editing the ASCII
			self.system.log(Exception("Cannot Edit ASCII Values"))
	
	
	def get_data(self, addr, num_rows):
		if self.align:
			# Jump to the next aligned address
			addr -= addr%(self.num_words * self.num_elems)
		
		# Read the data from the board
		out = []
		data = iter(self.system.read_memory(self.memory,
		                                    self.num_words,
		                                    addr,
		                                    num_rows * self.num_elems))
		
		for row in range(num_rows):
			addr = self.mask_addr(addr)
			blocks_formatted = []
			ascii_formatted = ""
			
			for element in range(self.num_elems):
				value = data.next()
				
				block_formatted = format_number(value, self.element_size)
				blocks_formatted.append(block_formatted)
				
				ascii_formatted += format_ascii(value, self.element_size)
			
			out.append((addr, self.num_words * self.num_elems, blocks_formatted + [ascii_formatted]))
			addr += self.num_words * self.num_elems
		
		return out



class DisassemblyTable(MemoryTable):
	
	def __init__(self, system, memory, assembler, disassembler, align = True):
		"""
		A MemoryTable which simply fetches blocks of the given number of memory
		words with no additional data.
		
		disassembler is the Disassembler to use
		
		align indicates whether displayed rows should be aligned to instructions
		(True) or whether rows should start from the requested address exactly
		(False). Not currently supported: all assemblers output aligned.
		"""
		MemoryTable.__init__(self, system, memory, align)
		
		self.assembler    = assembler
		self.disassembler = disassembler
	
	
	def get_columns(self):
		return ["Instruction", "Disassembly (%s)"%self.disassembler.name]
	
	
	def set_cell(self, addr, row, column, new_data):
		# Re-run the disassembler up to the requested row to find the address of
		# the row. (How wasteful!)
		addr, length, _ = self.get_data(addr, row+1)[-1]
		
		if column == 0:
			try:
				# Try and write the new value
				value = self.system.evaluate(new_data)
				self.system.write_memory(self.memory, length, addr, [value])
			except Exception, e:
				# The user entered something invalid, ignore the edit
				self.system.log(e, True)
		
		else:
			try:
				# Try and assemble the instruction
				# XXX: TODO: Add symbol table
				value = self.assembler.assemble_instruction(new_data, length, addr)
				self.system.write_memory(self.memory, length, addr, [value])
			except Exception, e:
				# Some assembler error
				self.system.log(e, True)
	
	
	def get_data(self, addr, num_rows):
		addr = self.mask_addr(addr)
		
		def memory_read(addr, num_words):
			return self.system.read_memory(self.memory, num_words, addr, 1)
		
		# XXX: This should at some point be extended to support areas of
		# memory/starting disassembly from a certain address.
		program_start_addr = 0
		
		# Disassemble
		disassembly = self.disassembler.disassemble(memory_read,
		                                            program_start_addr,
		                                            addr, num_rows)
		# Output
		out = []
		for addr, width_bits, instr, mnemonic in disassembly:
			addr = self.mask_addr(addr)
			formatted = format_number(instr, width_bits)
			out.append((addr, width_bits/self.memory.word_width_bits, [formatted, mnemonic]))
		
		return out
