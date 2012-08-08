#!/usr/bin/env python

"""
Assembler and loader functions provided as a mixin for the System.
"""

import os


class AssemblerLoaderMixin(object):
	
	def __init__(self):
		self.source_filename = None
		self.image_filename  = None
	
	
	def set_source_filename(self, filename):
		"""
		Set the source file to be assembled
		"""
		self.source_filename = filename
		self.image_filename  = None
	
	def set_image_filename(self, filename):
		"""
		Set the image file to be loaded
		"""
		self.image_filename = filename
	
	
	def get_source_filename(self):
		"""
		The source file to be assembled
		"""
		return self.source_filename
	
	def get_image_filename(self):
		"""
		The image file to be loaded
		"""
		return self.image_filename
	
	
	def assemble(self):
		"""
		Assemble the current source file
		"""
		# XXX: TODO: Allow a choice of assemblers and memories for now chose the
		# default
		memory = self.architecture.memories[0]
		assember, _ = memory.assemblers[0]
		
		try:
			self.image_filename = assember.assemble(self.source_filename)
		except Exception, e:
			self.log(e, flag = True)
	
	
	def _load_lst(self, memory, data):
		"""
		Load .lst format data into the given memory. Returns a generator that yields
		tuples (amount_read, total) indicating progress.
		"""
		try:
			# Parse the input file
			to_write = {}
			for line in data.strip().split("\n"):
				addr, val = map(str.strip, line.split(":"))
				
				val = val.split(";")[0].strip()
				
				addr = int(addr.split()[-1], 16)
				
				if val != "":
					# XXX: Assumes that each entry has exactly one word
					to_write[addr] = [int(val, 16)]
			
			# Write the data to the memory
			length = len(to_write)
			for num, (addr, values) in enumerate(to_write.iteritems()):
				self.write_memory(memory, 1, addr, values)
				yield (num, length)
			
		except Exception, e:
			self.log(e, flag = True)
	
	
	def load_image(self):
		"""
		Loads the current image file.
		"""
		for _ in self.load_image_():
			pass
	
	
	def load_image_(self):
		"""
		Loads the current image file. Returns a generator that yields tuples
		(amount_read, total) indicating progress or yields None when done.
		"""
		# XXX: TODO: Allow a choice of memories. For now chose the default.
		memory = self.architecture.memories[0]
		
		try:
			_, ext = os.path.splitext(self.image_filename)
			
			# Select a loader to use
			loaders = {
				".lst": self._load_lst
			}
			if ext not in loaders:
				raise Exception("Images in %s format not supported."%ext)
			loader = loaders[ext]
			
			# Load the image
			return loader(memory, open(self.image_filename, "r").read())
			
		except Exception, e:
			self.log(e, flag = True)
