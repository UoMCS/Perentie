#!/usr/bin/env python

"""
A STUMP assembler
"""

import os
from subprocess import Popen, PIPE

from base import Assembler


class MU0Assembler(Assembler):
	
	def __init__(self):
		Assembler.__init__(self)
		self.name = "MU0"
	
	
	def assemble(self, input_filename):
		# Get the output filename
		filename, ext = os.path.splitext(input_filename)
		output_filename = "%s.kmd"%filename
		
		# Start the assembler as a child-process (Capture stderr for errors)
		args = ["mu0asm", "-lk", output_filename, input_filename]
		assembler = Popen(args, stdout = PIPE)
		
		# Get the errors and wait for assembly to finish
		errors = assembler.stdout.read()
		return_code = assembler.wait()
		
		if return_code != 0:
			raise Exception("Assembly Failed:\n%s"%errors)
		
		return output_filename
