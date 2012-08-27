#!/usr/bin/env python

"""
Assembler and loader functions provided as a mixin for the System.

The reason filenames are specified in the slightly odd way they are is to allow
assemblers to set the loader file name in a simple way. Its not ideal but it
works.
"""

import os


class AssemblerLoaderMixin(object):
	
	def __init__(self):
		self.source_filename = None
		self.image_filename  = None
		
		# Relates memories to dicts which relate addresses to (width_words, value,
		# source_lines) where width_words is the number of memory words covered by
		# the source, value is the integer value in memory at this position and
		# source_lines is a list of strings containing a line of source code
		self.image_source = {}
		
		# A dictionary relating memories to dicts mapping symbol names to (value,
		# type) pairs.
		self.image_symbols = {}
	
	
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
		assember = memory.assemblers[0]
		
		try:
			self.image_filename = assember.assemble(self.source_filename)
		except Exception, e:
			self.log(e, True, "Assemble File")
	
	
	def _load_bin(self, memory, data):
		"""
		Load a raw binary data file into the given memory. Returns a generator that
		yields tuples (amount_read, total) indicating progress.
		"""
		try:
			to_write = []
			while data:
				word = data[:memory.word_width_bits / 8]
				data = data[memory.word_width_bits / 8:]
				num = 0
				for byte in word[::-1]:
					num <<= 8
					num  |= ord(byte)
				to_write.append(num)
			
			# Write the data to the memory
			length = len(to_write)
			for addr, word in enumerate(to_write):
				self.write_memory(memory, 1, addr, [word])
				yield (addr, length)
			
		except Exception, e:
			self.log(e, True, "Load Binary File")
	
	
	def _load_lst(self, memory, data):
		"""
		Load .lst format data into the given memory. Returns a generator that yields
		tuples (amount_read, total) indicating progress.
		"""
		try:
			# Parse the input file
			to_write = {}
			image_source = {}
			for line in data.strip().split("\n"):
				addr,_, val = map(str.strip, line.partition(":"))
				
				val,has_source,src = map(str.strip, val.partition(";"))
				
				# Remove spaces between words
				val = val.replace(" ","")
				
				addr = int(addr.split()[-1], 16)
				
				# XXX: Assumes that each entry has exactly one word
				if has_source:
					if addr not in image_source:
						image_source[addr] = (1, # XXX: Wrong width if a multi-word entry
						                      int(val,16) if val else 0,
						                      [src])
					else:
						image_source[addr] = (image_source[addr][0],
						                      image_source[addr][1] if not val else int(val, 16),
						                      image_source[addr][2] + [src])
				
				while val != "":
					to_write[addr] = [int(val[:memory.word_width_bits/4], 16)]
					addr += 1
					val = val[memory.word_width_bits/4:]
			
			# Set the source listing
			self.image_source[memory] = image_source
			
			# Write the data to the memory
			length = len(to_write)
			for num, (addr, values) in enumerate(to_write.iteritems()):
				self.write_memory(memory, 1, addr, values)
				yield (num, length)
			
		except Exception, e:
			self.log(e, True, "Load LST File")
	
	
	def _load_kmd(self, memory, data):
		"""
		Load .kmd format data into the given memory. Returns a generator that yields
		tuples (amount_read, total) indicating progress.
		"""
		# The number of nybles per memory word
		word_nybles = memory.word_width_bits/4
		
		try:
			# Check for the magic number
			if data[:4] != "KMD\n":
				raise Exception("KMD file magic number missing!")
			data = data[4:]
			
			# The symbol and data tables are seperated by an empty line
			data,_, symbol_data = data.partition("\n\n")
			
			# Parse the input file
			to_write = {}
			image_source = {}
			image_symbols = {}
			for line in data.strip().split("\n"):
				addr_str,_, val_src = map(str.strip, line.partition(":"))
				
				try:
					addr = int(addr_str, 16)
				except ValueError:
					# We have a line where the source was wrapped and thus there is no
					# address
					val_src = addr_str
				
				vals,_, src      = map(str.strip, val_src.partition(";"))
				
				# Remove spaces between units
				vals = vals.split(" ")
				
				# Add the source line to
				if addr not in image_source:
					image_source[addr] = (sum(map(len, vals))/word_nybles,
					                      int("".join(vals) or "0", 16),
					                      [src])
				else:
					image_source[addr] = (image_source[addr][0] + sum(map(len, vals))/word_nybles,
					                      image_source[addr][1] if not vals else int("".join(vals) or "0", 16) ,
					                      image_source[addr][2] + [src])
				
				# Warning: This will silently drop words which are smaller than a memory
				# word
				for val in vals:
					width_words = len(val)/word_nybles
					val         = int(val, 16) if width_words else 0
					for word in range(width_words):
						to_write[addr] = val>>(word*memory.word_width_bits) & ((1<<memory.word_width_bits)-1)
						addr += 1
			
			# Parse the symbol table
			for line in symbol_data.strip().split("\n")[1:]:
				line_parts = line.split(" ")
				symbol = line_parts[1]
				value,_,symbol_type = (" ".join(line_parts[2:])).lstrip(" ").partition("  ")
				image_symbols[symbol] = (int(value, 16), symbol_type)
			
			# Store the source & symbols
			self.image_source[memory]  = image_source
			self.image_symbols[memory] = image_symbols
			
			# Write the data to the memory
			length = len(to_write)
			for num, (addr, value) in enumerate(to_write.iteritems()):
				self.write_memory(memory, 1, addr, [value])
				yield (num, length)
			
		except Exception, e:
			self.log(e, True, "Load KMD File")
	
	
	def _load_elf(self, memory, data):
		"""
		Load .elf format data into the given memory. Returns a generator that yields
		tuples (amount_read, total) indicating progress.
		"""
		try:
			# Read the data from the elf-file
			from elftools.elf.elffile import ELFFile
			from StringIO import StringIO
			data_sections = {}
			for section in ELFFile(StringIO(data)).iter_sections():
				if section["sh_type"] == "SHT_PROGBITS":
					data_sections[section["sh_addr"]] = section.data()
			
			# Write the data to the memory
			length = sum(map(len, data_sections.itervalues()))
			num = 0
			for addr, values in data_sections.iteritems():
				for byte in values:
					self.write_memory(memory, 1, addr, [ord(byte)])
					addr += 1
					num += 1
					yield (num, length)
			
		except Exception, e:
			self.log(e, True, "Load ELF File")
	
	
	def load_image(self):
		"""
		Loads the current image file.
		"""
		for _ in self.load_image_():
			pass
	
	
	def get_loaders(self):
		return {
			".lst": self._load_lst,
			".kmd": self._load_kmd,
			".elf": self._load_elf,
			".bin": self._load_bin,
		}
	
	
	def get_loader_formats(self):
		return self.get_loaders().keys()
	
	
	def load_image_(self):
		"""
		Loads the current image file. Returns a generator that yields tuples
		(amount_read, total) indicating progress or yields None when done.
		"""
		# XXX: TODO: Allow a choice of memories. For now chose the default.
		memory = self.architecture.memories[0]
		
		try:
			_, ext = os.path.splitext(self.image_filename)
			ext = ext.lower()
			
			# Select a loader to use (default to a raw binary)
			loader = self.get_loaders().get(ext, self._load_bin)
			
			# Clear the symbol & source listings
			self.image_source = {}
			self.image_symbols = {}
			
			# Load the image
			for val in loader(memory, open(self.image_filename, "r").read()):
				yield val
			
			# Update the symbol list in the evaluator
			self.evaluator_update_symbols()
			
		except Exception, e:
			self.log(e, True, "Load Memory Image")
