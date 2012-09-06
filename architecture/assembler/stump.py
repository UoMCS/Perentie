#!/usr/bin/env python

"""
A STUMP assembler
"""

import os
from subprocess import Popen, PIPE

from base import Assembler

from StringIO import StringIO


class STUMPAssembler(Assembler):
	
	def __init__(self):
		Assembler.__init__(self)
		self.name = "STUMP"
	
	
	def assemble(self, input_filename):
		# Get the output filename, chop off the .s, replace with lst
		output_filename, ext = os.path.splitext(input_filename)
		if ext != ".s":
			output_filename += ext
		output_filename = "%s.kmd"%output_filename
		
		# Start the assembler as a child-process (Capture stderr for errors)
		args = ["sasm", "-lk", output_filename, input_filename]
		output = StringIO()
		assembler = Popen(args, stdout = PIPE)
		
		# Get the errors and wait for assembly to finish
		errors = assembler.stdout.read()
		return_code = assembler.wait()
		
		if return_code != 0:
			raise Exception("Assembly Failed:\n%s"%errors)
		
		return output_filename
