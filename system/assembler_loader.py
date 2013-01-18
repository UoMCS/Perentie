#!/usr/bin/env python

"""
Assembler and loader functions provided as a mixin for the System.

The reason filenames are specified in the slightly odd way they are is to allow
assemblers to set the loader file name in a simple way. Its not ideal but it
works.
"""

import os
import re

from math import ceil

from collections import defaultdict


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
		
		# A regular expression matching a line of a list file
		lst_line_re = re.compile(r"\s*("
		                           +r"(?P<address>[0-9a-f]+)"              # Address
		                           +r"\s*:\s*"                             # :
		                           +r"(?P<data>[0-9a-f]+(\s+[0-9a-f]+)*)?" # Data
		                         +r")?\s*("
		                           +r"; "                                  # ;
		                           +r"(?P<comment>.*)"                     # Comment
		                         +r")?", re.I)
		
		try:
			# Data to be written to memory as {addr:(size_words, value_int)}.
			to_write = {}
			
			# Source lines as a tuple as self.image_source would store
			image_source = defaultdict((lambda: [0, 0, []]))
			
			# Address to which next read values should be stored
			addr = 0
			
			# Parse the list file line-by-line
			for line_num, line in enumerate(data.strip().split("\n")):
				# Match the line against the regular expression to extract the relevent
				# fields and check for bad data
				match = lst_line_re.match(line)
				if not match:
					raise Exception("Invalid listing on line %d: %s"%(line_num, repr(line)))
				
				# Set the address if one was present (continue from last if not)
				if match.group("address"):
					addr = int(match.group("address"), 16)
				
				# The data contained in the line (keep as hex strings as these indicate
				# the size of the words to write)
				if match.group("data"):
					data = filter(None, match.group("data").split())
				else:
					data = []
				
				size = 0
				for block in data:
					# 4 bits per hex-char
					block_width_bits = len(block)*4
					words = int(ceil(float(block_width_bits) / memory.word_width_bits))
					
					# Make sure the address isn't being re-defined
					if addr in to_write:
						raise Exception("Address 0x%08X redefined on line %d: %s"%(addr, line_num, line))
					
					# Set the data to write for this address
					to_write[addr] = (words, int(block, 16))
					
					addr += words
					size += words
				
				# A source listing may be present as a comment in the lst file
				src = match.group("comment")
				if src is not None:
					# All preceeding lines with the same address should have had no data
					# in so we can happily overwrite the size and data here
					image_source[addr-size][0] = size
					image_source[addr-size][1] = 0 if not data else int("".join(data[::-1]), 16)
					# Preceeding lines may have added source lines, we should add ours to
					# the list.
					image_source[addr-size][2].append(src)
				
			# Set the source listing and symbols
			self.image_source[memory]  = image_source
			self.image_symbols[memory] = {}
			
			# Write the data to the memory
			length = len(to_write)
			for num, (addr, (words, data)) in enumerate(to_write.iteritems()):
				self.write_memory(memory, words, addr, [data])
				yield (num, length)
			
		except Exception, e:
			self.log(e, True, "Load LST File")
	
	
	def _load_kmd(self, memory, data):
		"""
		Load .kmd format data into the given memory. Returns a generator that yields
		tuples (amount_read, total) indicating progress.
		"""
		
		try:
			# Check for the magic number
			if data[:4] != "KMD\n":
				raise Exception("KMD file magic number missing!")
			data = data[4:]
			
			# The symbol and data tables are seperated by an empty line
			data,_, symbol_data = data.partition("\n\n")
			
			# Load the program part of the file as a normal lst file (loads the device
			# and sets source)
			for num,length in self._load_lst(memory, data):
				yield (num,length)
			
			# Parse the symbol table (chopping off the heading row)
			image_symbols = {}
			for line in symbol_data.strip().split("\n")[1:]:
				line_parts = line.split(" ")
				symbol = line_parts[1]
				value,_,symbol_type = (" ".join(line_parts[2:])).lstrip(" ").partition("  ")
				image_symbols[symbol] = (int(value, 16), symbol_type)
			
			# Store the symbols
			self.image_symbols[memory] = image_symbols
		
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
