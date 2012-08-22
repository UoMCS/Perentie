#!/usr/bin/env python

"""
An ARM assembler
"""

import os
from subprocess import Popen, PIPE

from base import Assembler


class ARMAssembler(Assembler):
	
	def __init__(self):
		Assembler.__init__(self)
		self.name = "ARM"
	
	
	def assemble(self, input_filename):
		# Get the output filename, chop off the .s, replace with lst
		output_filename, ext = os.path.splitext(input_filename)
		if ext != ".s":
			output_filename += ext
		output_filename = "%s.kmd"%output_filename
		
		# Start the assembler as a child-process (Capture stderr for errors)
		args = ["aasm", "-lk", output_filename, input_filename]
		assembler = Popen(args, stderr = PIPE)
		
		# Get the errors and wait for assembly to finish
		errors = assembler.stderr.read()
		return_code = assembler.wait()
		
		if return_code != 0:
			raise Exception("Assembly Failed:\n%s"%errors)
		
		return output_filename
