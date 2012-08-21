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
		# Get the output filename
		# Chop off the .s (as sasm does)
		filename, ext = os.path.splitext(input_filename)
		if ext != ".s":
			filename += ext
		output_filename = "%s.lst"%filename
		
		# Start the assembler as a child-process (Capture stderr for errors)
		args = ["sasm", input_filename, "-l"]
		assembler = Popen(args, stderr = PIPE)
		
		# Get the errors and wait for assembly to finish
		errors = assembler.stderr.read()
		return_code = assembler.wait()
		
		if return_code != 0:
			raise Exception("Assembly Failed:\n%s"%errors)
		
		# Stick the source in the comment at the end of each listing line. SASM
		# produces list files which correspond line-for-line with the source
		src = open(input_filename,"r").read().split("\n")
		lst = open(output_filename,"r").read().split("\n")
		
		lst_file = open(output_filename,"w")
		for src_line, lst_line in zip(src,lst):
			if lst_line.strip():
				lst_file.write("%s;%s\n"%(lst_line, src_line))
		lst_file.close()
		
		return output_filename
