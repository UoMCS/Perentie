#!/usr/bin/env python

"""
A set of device accessor functions provided as a mixin for the System. Provides
a cleaner, memoised interface to the device meaning that certain repeated
requests for the same values are not made.

If an error occurs when accessing a feature, it should be logged and a "default"
value returned instead (e.g. zeros).

This interface is not complete and is being added to as required. The back-end
should only be accessed within the program via this interface so if a feature
you need isn't available, please add it.
"""

from back_end.exceptions import BackEndError
from back_end.util       import i2b, b2i, bits_to_bytes

# XXX Bodges for the back-end's limitations
from back_end.bodge import xxx_pad_width



class DeviceMixin(object):
	"""
	Accessor functions, with memoised acceess, to the device.
	"""
	
	# Number of NOP commands to send to flush out the command channel
	NUM_NOPS = 100
	
	
	def __init__(self):
		self.clear_cache()
	
	
	def clear_cache(self):
		"""
		Empties the cache of board responses
		"""
		self.cached_registers = {}
	
	
	def resync(self):
		"""
		Checks to ensure the board is connected and synchronised. On failure, rasies
		an exception.
		
		XXX This function should check if the board connected has changed after
		having to resynchronise. If it has, currently wierdness will occur and go
		undetected. This should be fixed.
		"""
		try:
			# Try pinging the device
			self.back_end.ping()
		except BackEndError:
			# If that fails, flush the comms with nops and try again. If the channel
			# is not working then this command will raise an exception and bubble out.
			for _ in range(DeviceMixin.NUM_NOPS):
				self.back_end.nop()
			
			# Try once again to ping, if this fails, let the exception bubble through.
			self.back_end.ping()
	
	
	def get_cpu_type(self):
		"""
		Get the processor (type, sub_type). If there is an error, returns (-1,-1)
		"""
		try:
			self.resync()
			cpu_type, _, _ = self.back_end.get_board_definition()
			return cpu_type
		except BackEndError, e:
			self.log(e)
			return (-1, -1)
	
	
	def read_register(self, register):
		"""
		Read a register as given in the Architecture. Returns -1 on error.
		"""
		# Get the value from the cache if possible
		if register in self.cached_registers:
			return self.cached_registers[register]
		
		try:
			self.resync()
			
			# Read the register
			width_bytes = bits_to_bytes(xxx_pad_width(register.width_bits))
			addr        = register.addr
			length      = 1
			value = b2i(self.back_end.register_read(width_bytes, addr, length))
			
			# Cache and return the value
			self.cached_registers[register] = value
			return value
		
		except BackEndError, e:
			self.log(e)
			return -1
	
	
	def write_register(self, register, value):
		"""
		Write a register as given in the Architecture.
		"""
		# Remove the value from the cache (when re-reading read the value from the
		# device in-case the register is changed on write.
		if register in self.cached_registers:
			del self.cached_registers[register]
		
		try:
			self.resync()
			
			# Write the register
			width_bytes = bits_to_bytes(xxx_pad_width(register.width_bits))
			addr        = register.addr
			length      = 1
			data        = i2b(value, width_bytes)
			self.back_end.register_write(width_bytes, addr, data)
		
		except BackEndError, e:
			self.log(e)

	
	def read_memory(self, memory, elem_size_words, addr, length):
		"""
		Read from a memory as given in the Architecture. Returns a list of elements
		as integers of the number of words specified. If a location cannot be read,
		-1s are returned.
		"""
		try:
			self.resync()
			
			# Size of elements to read
			elem_size_bits = elem_size_words * memory.word_width_bits
			width_bytes = bits_to_bytes(xxx_pad_width(elem_size_bits))
			
			# Read the data from memory
			data = self.back_end.memory_read(memory.index, width_bytes, addr, length)
			
			# Decode into ints
			out = []
			for element in range(length):
				out.append(b2i(data[:width_bytes]))
				data = data[width_bytes:]
			
			# Return the value
			return out
		
		except BackEndError, e:
			self.log(e)
			return [-1] * length
	
	
	def write_memory(self, memory, elem_size_words, addr, data):
		"""
		Write to a memory as given in the Architecture.
		"""
		# Remove the value from the cache (when re-reading read the value from the
		# device in-case the register is changed on write.
		try:
			self.resync()
			
			# Size of elements to write
			elem_size_bits = elem_size_words * memory.word_width_bits
			width_bytes = bits_to_bytes(xxx_pad_width(elem_size_bits))
			
			# Decode from ints
			out = ""
			for element in data:
				out += i2b(element, width_bytes)
			
			# Write the data from memory
			data = self.back_end.memory_write(memory.index, width_bytes, addr, out)
		
		except BackEndError, e:
			self.log(e)
