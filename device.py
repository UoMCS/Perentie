#!/usr/bin/env python

"""
A set of device accessor functions provided as a mixin for the System. Provides
a cleaner, memoised interface to the device meaning that certain repeated
requests for the same values are not made.

Unless otherwise stated, all functions are thread-safe and can be used, for
example within functions decorated by RunInBackground.

If an error occurs when accessing a feature, it should be logged and a valid
"default" value returned instead (e.g. -1).

This interface is not complete and is being added to as required. The back-end
should only be accessed within the program via this interface so if a feature
you need isn't available, please add it.
"""

from threading import Lock

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
	
	# Max number bytes to read to flush the input channel
	NUM_BLANK_READS = 10000
	
	
	# Status constants
	STATUS_ERROR              = -1
	STATUS_RESET              = 0x00
	STATUS_BUSY               = 0x01
	STATUS_STOPPED            = 0x40
	STATUS_STOPPED_BREAKPOINT = 0x41
	STATUS_STOPPED_WATCHPOINT = 0x42
	STATUS_STOPPED_MEM_FAULT  = 0x43
	STATUS_STOPPED_PROG_REQ   = 0x44
	STATUS_RUNNING            = 0x80
	STATUS_RUNNING_SWI        = 0x81
	
	
	def __init__(self):
		self.device_lock = Lock()
		self.cache_lock = Lock()
		
		self.clear_cache()
	
	
	def clear_cache(self):
		"""
		Empties the cache of board responses
		"""
		with self.cache_lock:
			self.cached_registers = {}
	
	
	def resync(self):
		"""
		Checks to ensure the board is connected and synchronised. On failure, rasies
		an exception.
		
		Warning: this method is not thread safe!
		
		XXX This function should check if the board connected has changed after
		having to resynchronise. If it has, currently wierdness will occur and go
		undetected. This should be fixed.
		"""
		try:
			# Try pinging the device
			self.back_end.ping()
		except BackEndError:
			# If that fails, flush the comms with nops and try again. If the channel
			# is allowing writes then this command will raise an exception and bubble
			# out.
			for _ in range(DeviceMixin.NUM_NOPS):
				self.back_end.nop()
			
			# Absorb any random data which may be in the read buffer
			self.back_end.ignore(DeviceMixin.NUM_BLANK_READS)
			
			# Try once again to ping, if this fails, let the exception bubble through.
			self.back_end.ping()
	
	
	def get_cpu_type(self):
		"""
		Get the processor (type, sub_type). If there is an error, returns (-1,-1)
		"""
		with self.device_lock:
			try:
				self.resync()
				cpu_type, _, _ = self.back_end.get_board_definition()
				return cpu_type
			except BackEndError, e:
				self.log(e)
				return (-1, -1)
	
	
	def get_peripheral_ids(self):
		"""
		Get a list of peripheral IDs as (id, sub_id) for all peripherals.
		"""
		with self.device_lock:
			try:
				self.resync()
				_, peripheral_ids, _ = self.back_end.get_board_definition()
				return peripheral_ids
			except BackEndError, e:
				self.log(e)
				return []
	
	
	def read_register(self, register):
		"""
		Read a register as given in the Architecture. Returns -1 on error.
		"""
		with self.device_lock:
			# Get the value from the cache if possible
			with self.cache_lock:
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
				with self.cache_lock:
					self.cached_registers[register] = value
					return value
			
			except BackEndError, e:
				self.log(e)
				return -1
	
	
	def write_register(self, register, value):
		"""
		Write a register as given in the Architecture.
		"""
		with self.device_lock:
			# Remove the value from the cache (when re-reading read the value from the
			# device in-case the register is changed on write.
			with self.cache_lock:
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
		with self.device_lock:
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
		with self.device_lock:
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
	
	
	def reset(self):
		with self.device_lock:
			try:
				self.back_end.reset()
			except BackEndError, e:
				self.log(e)
	
	
	def run(self, max_steps = 0,
	        halt_on_watchpoint = True, halt_on_breakpoint = True,
	        halt_on_mem_fault = False, step_over_swi = False,
	        step_over_bl = False, break_on_first_instruction = True):
		with self.device_lock:
			try:
				self.back_end.run(max_steps,
													halt_on_watchpoint, halt_on_breakpoint, halt_on_mem_fault,
													step_over_swi, step_over_bl,
													break_on_first_instruction)
			except BackEndError, e:
				self.log(e)
	
	
	def stop(self):
		with self.device_lock:
			try:
				self.back_end.stop_execution()
			except BackEndError, e:
				self.log(e)
	
	
	def pause_execution(self):
		with self.device_lock:
			try:
				self.back_end.pause_execution()
			except BackEndError, e:
				self.log(e)
	
	
	def continue_execution(self):
		with self.device_lock:
			try:
				self.back_end.continue_execution()
			except BackEndError, e:
				self.log(e)
	
	
	def get_status(self):
		"""
		Get the status of the board. Returns a tuple
		(status, steps_remaining, steps_since_reset).
		"""
		with self.device_lock:
			try:
				return self.back_end.get_status()
			except BackEndError, e:
				self.log(e)
				return (DeviceMixin.STATUS_ERROR, -1, -1)
