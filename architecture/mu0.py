#!/usr/bin/env python

"""
MU0 specific definition of a system.
"""

from base import Architecture

from register import RegisterBank, Register, Pointer, BitField
from memory   import Memory

from disassembler.mu0 import MU0Disassembler
from assembler.mu0    import MU0Assembler


class MU0(Architecture):
	
	def __init__(self, *args, **kwargs):
		"""
		Define the MU0 system's memory, registers etc.
		"""
		Architecture.__init__(self, *args, **kwargs)
		
		self.name = "MU0"
		
		self.word_width_bits = 16
		
		memory = Memory(
			0,                   # The zeroth and only memory
			["Memory", "Mem",
			 "memory", "mem"],   # Names for the main/only memory
			12,                  # 12-bit addresses
			16,                  # 16-bit memory words
			[(MU0Assembler(), MU0Disassembler())]) # Use the MU0 (dis)assembler
		
		self.memories.append(memory)
		
		self.register_banks.append(RegisterBank(["Registers", "Reg",
		                                         "registers", "reg"], [
				Register(["Accumulator", "ACC",
				          "accumulator", "acc"],  # Named 'Accumulator' aka 'ACC'
				         16,                      # 16 bits wide
				         0,                       # At address 0 in the register address space
				         Pointer([memory])),      # May point into memory
				
				Register(["PC", "pc"],            # Named 'PC'
				         12,                      # 12 bits wide
				         1,                       # At address 1 in the register address space
				         Pointer([memory], "PC")),# Points into memory as the PC
				
				Register(["Flags", "flags"],      # Flag register
				         2,                       # 2 bits wide
				         2,                       # At address 2 in the register address space
				         None,                    # Doesn't point into memory
				         BitField(((0, "Z"),      # Accumulator zero bit
				                   (1, "N"))))    # Accumulator sign bit
			])
		)
