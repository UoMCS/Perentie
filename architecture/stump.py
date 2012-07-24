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
		
		self.memories.append(Memory(
			["Memory", "Main", "Store"], # Names for the main/only memory
			16,                          # 16-bit address bus
			16,                          # 16-bit memory words
			[STUMPDisassembler()])       # Use the STUMP disassembler
		)
		
		self._define_registers()
	
	
	def _define_registers(self):
		"""
		Define all the STUMP's registers.
		"""
		registers = []
		
		# Define R0
		registers.append(Register(
			["R0"], # Named R0
			16,     # 16-bits wide
			0,      # At address 0 in the register address space
			None)   # As this is always 0, don't display a pointer
		)
		
		# Define R1-R6
		for n in range(1,7):
			registers.append(Register(
				["R%d"%n],    # Named Rn for each 1-6
				16,           # 16-bits wide
				n,            # At address n in the register address space
				Pointer([0])) # May point into memory 0 (the only memory)
			)
		
		# Define R7
		registers.append(Register(
			["PC", "R7"],       # The PC (aka R7)
			16,                 # 16-bits wide
			7,                  # At address 7 in the register address space
			Pointer([0], "PC")) # Points into memory 0 as the PC
		)
		
		# Define the flags
		registers.append(Register(
			["CC", "Flags"],      # CC (aka the flags)
			4,                    # 4-bits
			8,                    # At address 8 in the register address space
			None,                 # Not a pointer
			BitField(((0, "C"),
			          (1, "V"),
			          (2, "Z"),
			          (3, "N")))) # The CC is a simple bit field with the flags defined
		)
		
		self.register_banks.append(RegisterBank(["Registers"], registers))

