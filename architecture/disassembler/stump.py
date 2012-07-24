#!/usr/bin/env python

"""
A STUMP disassembler
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


def sign_extend(value, bits):
	"""
	Sign extend the b-bit number n into a python integer
	"""
	return value | ((-1<<length) if bool(value >> length-1) else 0)


class STUMPDisassembler(Disassembler):
	
	INSTR_NAMES = {
		0b000: "ADD",
		0b001: "ADC",
		0b010: "SUB",
		0b011: "SBC",
		0b100: "AND",
		0b101: "OR",
		0b110: "",
		0b111: "B",
	}
	
	BRANCH_TYPES = {
		0b0000: "AL",
		0b0001: "NV",
		0b0010: "HI",
		0b0011: "LS",
		0b0100: "CC",
		0b0101: "CS",
		0b0110: "NE",
		0b0111: "EQ",
		0b1000: "VC",
		0b1001: "VS",
		0b1010: "PL",
		0b1011: "MI",
		0b1100: "GE",
		0b1101: "LT",
		0b1110: "GT",
		0b1111: "LE",
	}
	
	SHIFTS = {
		0b00 : "",
		0b01 : ", asr",
		0b10 : ", ror",
		0b11 : ", rrc"
	}
	
	
	def __init__(self):
		Disassembler.__init__(self)
		self.name = "STUMP"
		
	
	def _disassemble_instr(self, instr):
		s = ""
		
		# Decode name
		s += STUMPDisassembler.INSTR_NAMES[instr >> 13]
		
		if instr >> 13 == 0b111: # Branch instruction
			# Add condition
			s += STUMPDisassembler.BRANCH_TYPES[(instr >> 8) & 0xF]
			
			# Pretty spacing
			s = s.ljust(4)
			
			# Add branch offset
			s += " %d"%(sign_extend(instr&0xFF, 8))
			return s
		
		elif instr >> 13 == 0b110: # Load/Store instruction
			if instr >> 11 & 0b1:
				s += "ST"
			else:
				s += "LD"
			
			# Pretty spacing
			s = s.ljust(4)
			
			# Destination register
			s += " R%d, ["%((instr>>8) & 0b111)
		elif (instr >> 11) & 0b1: # Flag-setting function
			s += "S"
			
			# Pretty spacing
			s = s.ljust(4)
			
			# Destination register
			s += " R%d, "%((instr >> 8) & 0b111)
		else:
			# Pretty spacing
			s = s.ljust(4)
			
			# Destination register
			s += " R%d, "%((instr >> 8) & 0b111)
		
		# Source-A register
		s += "R%d, "%((instr >> 5) & 0b111)
		
		if (instr >> 12) & 0b1:
			# Immediate
			s += "#%d"%(sign_extend(instr&0b11111, 5))
		else:
			# Source-B register
			s += "R%d"%((instr>>2)&0b111)
			
			# Shift
			s += STUMPDisassembler.SHIFTS[instr & 0b11]
		
		
		if instr >> 13 == 0b110:
			# Close bracket for ld/st
			s += "]"
		
		return s
	
	
	def disassemble(self, memory_read, program_start_addr, start_addr, num_instrs):
		"""
		Disassembles an MU0 program
		"""
		
		disassembly = []
		
		for instr_num in range(num_instrs):
			instr = b2i(memory_read(16, start_addr, 1))
			disassembly.append((16, self._disassemble_instr(instr)))
		
		return disassembly



