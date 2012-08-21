#!/usr/bin/env python

"""
ARM specific definition of a system.
"""

from base import Architecture

from register import RegisterBank, Register, Pointer, BitField
from memory   import Memory

from assembler.arm import ARMAssembler


class ARM(Architecture):
	
	def __init__(self, *args, **kwargs):
		"""
		Define the ARM's system's memory, registers etc.
		"""
		Architecture.__init__(self, *args, **kwargs)
		
		self.name = "ARM"
		
		self.word_width_bits = 32
		
		memory = Memory(
			0,                   # The zeroth and only memory
			["Memory", "Mem",
			 "memory", "mem"],     # Names for the main/only memory
			32,                    # 32-bit address bus
			8,                     # 8-bit memory words
			[ARMAssembler()],      # Use the ARM assembler
			[])                    # TODO: add a disassembler

		self.memories.append(memory)
		
		self._define_register_bank(memory, ["Current", "current"], 0, True)
		self._define_register_bank(memory, ["User", "System",
		                                    "user", "system"], 32)
		self._define_register_bank(memory, ["Supervisor",
		                                    "supervisor"], 64)
		self._define_register_bank(memory, ["Abort",
		                                    "abort"], 96)
		self._define_register_bank(memory, ["Undefined", "undef",
		                                    "undefined", "undef"], 128)
		self._define_register_bank(memory, ["IRQ", "irq"], 160)
		self._define_register_bank(memory, ["FIQ", "FIQ"], 192)
	
	
	def _define_register_bank(self, memory, names, offset, pointers = False):
		"""
		Define a register-bank worth of registers.
		
		If pointers is true, add pointers
		"""
		registers = []
		
		# Define R0-R12
		for n in range(12 + 1):
			registers.append(Register(
				["R%d"%n,
				 "r%d"%n],         # Named Rn for each n
				32,                # 32-bits wide
				offset + n,        # At address n in the register address space
				Pointer([memory]) if pointers else None) # May point into memory
			)
		
		# Define "special" registers R13-R15
		for n, name in ((13, "SP"), (14, "LR"), (15, "PC")):
			registers.append(Register(
				[name, name.lower(),
				 "R%d"%n, "r%d"%n],    # Names
				32,                      # 16-bits wide
				offset + n,              # At address n in the register address space
				Pointer([memory], name) if pointers else None) # Points into memory as the type it is
			)
		
		# Define the flag registers
		# XXX: This is probably not correct (need to check jimulator for how to
		# access these fields correctly)
		for n, flag_name in enumerate(["CPSR", "SPSR"]):
			registers.append(Register(
				[flag_name, flag_name.lower()], # Name
				32,                             # 4-bits
				offset + 16 + n,                # At address 16/17 in the register address space
				None,                           # Not a pointer
				BitField(((31, "N"),
				          (30, "Z"),
				          (29, "C"),
				          (28, "V"),
				          (7,  "I"),
				          (6,  "F"),
				          (((4,0),), "Mode", {
				            0b10000: "User",
				            0b10001: "FIQ",
				            0b10010: "IRQ",
				            0b10011: "Supervisor",
				            0b10111: "Abort",
				            0b11011: "Undefined",
				          }))))
			)
		
		self.register_banks.append(RegisterBank(names, registers))


