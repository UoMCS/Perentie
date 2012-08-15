#!/usr/bin/env python

"""
An emulator back-end for the protocol. Starts a sub-process and connects the
standard input and output pipes to the read/write interface.
"""

from subprocess import Popen, PIPE

from base import BackEnd

class EmulatorBackEnd(BackEnd):
	
	def __init__(self, args):
		"""
		Starts the emulator specified in args as a sub-process. Args should be a
		valid shell command string.
		"""
		BackEnd.__init__(self)
		
		self.name = "Emulator"
		
		# Start the emulator as a child-process
		self.emulator = Popen(args,
		                      bufsize = -1,   # Produce a fully-buffered set of pipes
		                      stdin   = PIPE, # Source stdin from the protocol
		                      stdout  = PIPE, # Supply stdout to the protocol
		                      stderr  = None, # Stderr should not be redirected
		                      shell   = True) # Execute in a shell
	
	
	def read(self, length):
		return self.emulator.stdout.read(length)
	
	
	def write(self, data):
		self.emulator.stdin.write(data)
	
	
	def flush(self):
		self.emulator.stdin.flush()
	
	
	def close(self):
		self.emulator.stdin.close()
		self.emulator.stdout.close()
		self.emulator.kill()
