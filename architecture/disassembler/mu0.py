#!/usr/bin/env python

"""
An MU0 disassembler
"""

from disassembler import Disassembler


class MU0Disassembler(Disassembler):
	
	INSTRUCTIONS = {
		# Opcode: (mnemonic, has_argument)
		0x00: ("LDA", True),
		0x01: ("STA", True),
		0x02: ("ADD", True),
		0x03: ("SUB", True),
		0x04: ("JMP", True),
		0x05: ("JGE", True),
		0x06: ("JNE", True),
		0x07: ("STP", False),
	}
	
	
	def __init__(self):
		Disassembler.__init__(self)
		self.name = "MU0"
	
	
	def disassemble(self, memory_read, program_start_addr, start_addr, num_instrs):
		"""
		Disassembles an MU0 program
		"""
		
		disassembly = []
		
		for instr_num in range(num_instrs):
			instr = memory_read(start_addr, 1)[0]
			
			# Decode
			opcode   = instr >> 12
			argument = instr & ((1<<12) - 1)
			
			# Disassemble
			if opcode in MU0Disassembler.INSTRUCTIONS:
				mnemonic, has_argument = MU0Disassembler.INSTRUCTIONS[opcode]
				if has_argument:
					mnemonic += " 0x%03X"%(argument)
			else:
				# Unknown instruction
				mnemonic = "(unknown)"
			
			disassembly.append((start_addr, 16, instr, mnemonic))
			
			# Next instruction
			start_addr += 1
		
		return disassembly


