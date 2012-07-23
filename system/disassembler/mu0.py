#!/usr/bin/env python

"""
An MU0 disassembler
"""

from disassembler import Disassembler


def b2i(data):
	"""
	Convert a stream of bytes into a number
	"""
	out = 0
	for char in data[::-1]:
		out <<= 8
		out |= ord(char)
	return out



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
	
	def disassemble(self, memory_interface, program_start_addr, start_addr, num_instrs):
		"""
		Disassembles an MU0 program
		"""
		
		disassembly = []
		
		for instr_num in range(num_instrs):
			instr = b2i(memory_interface.read(start_addr, 16, 1))
			
			# Decode
			opcode   = instr >> 12
			argument = instr & ((1<<12) - 1)
			
			# Disassemble
			mnemonic, has_argument = MU0Disassembler.INSTRUCTIONS[opcode]
			if has_argument:
				mnemonic += " 0x%03X"%(argument)
			
			disassembly.append((16, mnemonic))
		
		return disassembly


