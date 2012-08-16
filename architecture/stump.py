#!/usr/bin/env python

"""
STUMP specific definition of a system.
"""

from base import Architecture

from register import RegisterBank, Register, Pointer, BitField
from memory   import Memory

from disassembler.stump import STUMPDisassembler
from assembler.stump    import STUMPAssembler


class STUMP(Architecture):
	
	# CPU Sub-type bottom-bytes which enable/disable register support
	SUBTYPE_REG_AND_MEM = 0x00
	SUBTYPE_MEMORY_ONLY = 0x01
	
	def __init__(self, cpu_type, cpu_subtype):
		"""
		Define the STUMP system's memory, registers etc.
		
		The subtype's bottom byte indicates whether memory and registers are
		available for debugging. The top byte indicates the number of 16-bit user
		registers.
		"""
		Architecture.__init__(self, cpu_type, cpu_subtype)
		
		self.name = "STUMP"
		
		self.word_width_bits = 16
		
		memory = Memory(
			0,                   # The zeroth and only memory
			["Memory", "Mem",
			 "memory", "mem"],     # Names for the main/only memory
			16,                    # 16-bit address bus
			16,                    # 16-bit memory words
			[(STUMPAssembler(), STUMPDisassembler())]) # Use the STUMP (dis)assembler

		self.memories.append(memory)
		
		if (cpu_subtype & 0xFF) != STUMP.SUBTYPE_MEMORY_ONLY:
			self._define_registers(memory)
		
		num_user_registers = ((cpu_subtype>>8) & 0xFF)
		if num_user_registers:
			self._define_user_registers(num_user_registers)
	
	
	def _define_registers(self, memory):
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

	def _define_user_registers(self, num_user_registers):
		"""
		Define the extra user registers.
		"""
		registers = []
		
		# Define R0
		for num in range(num_user_registers):
			registers.append(Register(
				[s%num for s in ["User%d", "U%d",
				                 "user%d", "u%d"]],
				16,      # 16-bits wide
				9 + num, # At address 9 in the register address space onwards
				None)    # Don't display a pointer (we don't know what the value is)
			)
		
		self.register_banks.append(RegisterBank(["Signals", "Sig",
		                                         "signals", "sig"], registers))

