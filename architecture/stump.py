#!/usr/bin/env python

"""
STUMP specific definition of a system.
"""

from base import Architecture

from register import RegisterBank, Register, Pointer, BitField
from memory   import Memory

from disassembler.stump import STUMPDisassembler


class STUMP(Architecture):
	
	def __init__(self):
		"""
		Define the STUMP system's memory, registers etc.
		"""
		Architecture.__init__(self)
		
		self.name = "STUMP"
		
		self.word_width_bits = 16
		
		memory = Memory(
			0,                   # The zeroth and only memory
			["Memory", "Mem",
			 "memory", "mem"],     # Names for the main/only memory
			16,                    # 16-bit address bus
			16,                    # 16-bit memory words
			[STUMPDisassembler()]) # Use the STUMP disassembler

		self.memories.append(memory)
		
		self._define_registers()
	
	
	def _define_registers(self):
		"""
		Define all the STUMP's registers.
		"""
		registers = []
		
		# Define R0
		registers.append(Register(
			["R0",
			 "r0"], # Named R0
			16,     # 16-bits wide
			0,      # At address 0 in the register address space
			None)   # As this is always 0, don't display a pointer
		)
		
		# Define R1-R6
		for n in range(1,7):
			registers.append(Register(
				["R%d"%n,
				 "r%d"%n],         # Named Rn for each 1-6
				16,                # 16-bits wide
				n,                 # At address n in the register address space
				Pointer([memory])) # May point into memory
			)
		
		# Define R7
		registers.append(Register(
			["PC", "R7",
			 "pc", "r7"],            # The PC (aka R7)
			16,                      # 16-bits wide
			7,                       # At address 7 in the register address space
			Pointer([memory], "PC")) # Points into memory as the PC
		)
		
		# Define the flags
		registers.append(Register(
			["CC", "Flags",
			 "cc", "flags"],      # CC (aka the flags)
			4,                    # 4-bits
			8,                    # At address 8 in the register address space
			None,                 # Not a pointer
			BitField(((3, "N"),
			          (2, "Z"),
			          (1, "V"),
			          (0, "C")))) # The CC is a simple bit field with the flags defined
		)
		
		self.register_banks.append(RegisterBank(["Registers", "Reg",
		                                         "registers", "reg"], registers))

