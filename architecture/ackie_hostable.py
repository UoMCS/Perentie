#!/usr/bin/env python

"""
A base class which defines an architecture which supports being hosted by the
'Ackie' ARM host program on the board.

Detauls of the architecture is gleaned from the CPU sub-type constant.  The
subtype's bottom byte indicates whether memory and registers are available for
debugging. The top byte indicates the number of 16-bit user registers.
"""

from base import Architecture

from register import RegisterBank, Register, Pointer, BitField


class AckieHostable(Architecture):
	
	# CPU Sub-type bottom-bytes which enable/disable register support
	SUBTYPE_REG_AND_MEM = 0x00
	SUBTYPE_MEMORY_ONLY = 0x01
	
	def __init__(self, *args, **kwargs):
		"""
		Define the MU0 system's memory, registers etc.
		"""
		Architecture.__init__(self, *args, **kwargs)
	
	
	def _define_all_registers(self):
		"""
		Causes all required registers to be defined.
		"""
		
		# If enabled, add the registers
		if self.registers_enabled:
			self._define_registers()
		
		# Add any user-defined registers
		if self.num_user_registers > 0:
			self._define_user_registers()
	
	
	@property
	def registers_enabled(self):
		"""
		Are registers enabled or is this a memory-only device?
		"""
		return (self.cpu_subtype & 0xFF) == AckieHostable.SUBTYPE_REG_AND_MEM
	
	
	@property
	def num_user_registers(self):
		"""
		The number of user-defined registers which come out of any extra bits of the
		scan path defined by the student.
		"""
		return (self.cpu_subtype>>8) & 0xFF
	
	
	def _define_registers(self):
		"""
		Called to add the architecture's built-in registers.
		"""
		raise NotImplementedError("_add_registers not implemented!")
		
	
	def _define_user_registers(self):
		"""
		Called to add the user registers dictated by the CPU subtype.
		"""
		registers = []
		for num in range(self.num_user_registers):
			registers.append(Register(
				[s%num for s in ["User%d", "U%d",
				                 "user%d", "u%d"]],
				16,      # 16-bits wide
				9 + num, # At address 9 in the register address space onwards
				None)    # Don't display a pointer (we don't know what the value is)
			)
		
		self.register_banks.append(RegisterBank(["Signals", "Sig",
		                                         "signals", "sig"], registers))
