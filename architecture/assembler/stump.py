#!/usr/bin/env python

"""
A STUMP assembler
"""

import os
from subprocess import Popen, PIPE

from base import Assembler


class STUMPAssembler(Assembler):
	
	def __init__(self):
		Assembler.__init__(self)
		self.name = "STUMP"
	
	
	def assemble(self, input_filename):
		# Start the assembler as a child-process (Capture stderr for errors)
		args = ["sasm", input_filename, "-l"]
		assembler = Popen(args, stderr = PIPE)
		
		# Get the errors and wait for assembly to finish
		errors = assembler.stderr.read()
		return_code = assembler.wait()
		
		if return_code != 0:
			raise Exception("Assembly Failed:\n%s"%errors)
		
		# Get the output filename
		# Chop off the .s (as sasm does)
		filename, ext = os.path.splitext(input_filename)
		if ext != ".s":
			filename += ext
		
		return "%s.lst"%filename
