#!/usr/bin/env python

"""
An MU0 assembler
"""

from base import Assembler


class MU0Assembler(Assembler):
	
	def __init__(self):
		Assembler.__init__(self)
		self.name = "MU0"
	
	
	def assemble(self, input_filename):
		raise NotImplementedError("No MU0 Assembler available")

