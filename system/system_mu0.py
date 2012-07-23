#!/usr/bin/env python

"""
MU0 specific definition of a system.
"""

from system import System

from register import RegisterBank, Register, Pointer, BitField
from memory   import Memory


class MU0System(System):
	
	def __init__(self):
		"""
		Define the STUMP system's memory, registers etc.
		"""
		System.__init__(self)
		
		self.name = "MU0"
		
		self.memories.append(Memory(
			["Memory", "Main", "Store"], # Names for the main/only memory
			12,                          # 12-bit addresses
			16)                          # 16-bit memory words
		)
		
		self.register_banks.append(RegisterBank(["Registers"], [
				Register(["Accumulator", "ACC"],  # Named 'Accumulator' aka 'ACC'
				         16,                      # 16 bits wide
				         0,                       # At address 0 in the register address space
				         Pointer([0])),           # May point into memory 0 (the only memory)
				
				Register(["PC"],                  # Named 'PC'
				         12,                      # 12 bits wide
				         1,                       # At address 1 in the register address space
				         Pointer([0], "PC")),     # Points into memory 0 as the PC
				
				Register(["Flags"],               # Flag register
				         2,                       # 2 bits wide
				         2,                       # At address 2 in the register address space
				         None,                    # Doesn't point into memory
				         BitField(((0, "Z"),      # Accumulator zero bit
				                   (1, "N"))))    # Accumulator sign bit
			])
		)
