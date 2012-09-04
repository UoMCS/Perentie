#!/usr/bin/env python

"""
An implementation of a KMD Comms Protocol master.

Spec: http://www.cs.manchester.ac.uk/resources/software/komodo/comms.html
"""

from exceptions     import *
from util.num_utils import *


class BackEnd(object):
	
	# Commands
	NOP                  = 0x00
	PING                 = 0x01
	GET_BOARD_DEFINITION = 0x02
	RESET                = 0x04
	
	# Peripherals (features)
	PERIPH_GET_STATUS      = 0x10
	PERIPH_SET_STATUS      = 0x11
	PERIPH_SEND_MESSAGE    = 0x12
	PERIPH_GET_MESSAGE     = 0x13
	PERIPH_DOWNLOAD_HEADER = 0x14
	PERIPH_DOWNLOAD_PACKET = 0x15
	
	# Execution control
	GET_STATUS         = 0x20
	STOP_EXECUTION     = 0x21
	PAUSE_EXECUTION    = 0x22
	CONTINUE_EXECUTION = 0x23
	
	# Trap manipulation
	TRAP_DEFINE      = 0x30
	TRAP_READ        = 0x31
	TRAP_SET_STATUS  = 0x32
	TRAP_READ_STATUS = 0x33
	
	# Memory transfers
	MEMORY_WRITE = 0x40
	MEMORY_READ  = 0x48
	
	# Program execution
	RUN = 0x80
	
	
	# Memory types
	MEMORY_MEMORY   = 0x00
	MEMORY_REGISTER = 0x10
	
	
	# Trap types
	TRAP_BREAKPOINT = 0x00
	TRAP_WATCHPOINT = 0x04
	TRAP_REGISTER   = 0x08
	
	# Trap condition types
	CONDITION_IN_RANGE = 0b10
	CONDITION_IN_MASK  = 0b11
	
	# Trap state set actions (bitmask 0, bitmask 1)
	TRAP_NOP        = (0,0)
	TRAP_DELETE     = (1,0)
	TRAP_DEACTIVATE = (0,1)
	TRAP_ACTIVATE   = (1,1)
	
	# Trap state read values (bitmask 0, bitmask 1)
	TRAP_NOT_IMPLEMENTED = (0,0)
	TRAP_NOT_DEFINED     = (1,0)
	TRAP_INACTIVE        = (0,1)
	TRAP_ACTIVE          = (1,1)
	
	
	# Defined statuses
	STATUS_RESET              = 0x00
	STATUS_BUSY               = 0x01
	STATUS_STOPPED            = 0x40
	STATUS_STOPPED_BREAKPOINT = 0x41
	STATUS_STOPPED_WATCHPOINT = 0x42
	STATUS_STOPPED_MEM_FAULT  = 0x43
	STATUS_STOPPED_PROG_REQ   = 0x44
	STATUS_RUNNING            = 0x80
	STATUS_RUNNING_SWI        = 0x81
	
	# Length of a peripheral download packet
	PACKET_LENGTH = 256
	
	
	def __init__(self):
		"""
		Create a protocol implementation.
		"""
		self.name = None
	
	
	def read(self, length):
		"""
		Read some data from the device
		"""
		raise NotImplementedError("BackEnd must implement read")
	
	
	def write(self, data):
		"""
		Write some data to the device
		"""
		raise NotImplementedError("BackEnd must implement write")
	
	
	def flush(self):
		"""
		Flush the output buffer (call after completing a command for which a
		response/action is expected).
		"""
		raise NotImplementedError("BackEnd must implement flush")
	
	
	def close(self):
		"""
		Close the pipe and kill the back-end.
		"""
		raise NotImplementedError("BackEnd must implement close!")
	
	
	def read_exactly(self, length):
		"""
		Read the exactly specified number of bytes from the device. Raises exception
		on failure. This is used to ensure that all data is read rather than
		returning too little data silently and causing wierd bugs elsewhere.
		"""
		data = self.read(length)
		
		if len(data) != length:
			raise ReadError("Got %d bytes, expected %d"%(len(data), length))
		
		return data
	
	
	def ignore(self, length):
		"""
		Ignores up-to a certain number if incomming bytes.
		"""
		self.read(length)
	
	
	def nop(self):
		"""
		Perform a NOP
		"""
		self.write(byte(BackEnd.NOP))
		self.flush()
	
	
	def ping(self):
		"""
		Ping the board. Returns the software version or raises a
		MalformedPingResponseException if the response is invalid.
		"""
		self.write(byte(BackEnd.PING))
		self.flush()
		
		# Expect back in form OK%02d
		response = self.read_exactly(4)
		
		# Check for OK
		if response[0:2] != "OK":
			raise MalformedPingResponseException(response)
		
		# Get version
		try:
			version = int(response[2:])
		except ValueError:
			raise MalformedPingResponseException(response)
		
		return version
	
	
	def get_board_definition(self):
		"""
		Get the details of the device's type. Returns a tuple
		((cpu_type, cpu_sub_type), features (a.k.a. peripherals), segments) or a
		MalformedResponseError if the length of the response is incorrect.
		"""
		self.write(byte(BackEnd.GET_BOARD_DEFINITION))
		self.flush()
		
		# Get the message length
		msg_length = b2i(self.read_exactly(2))
		actual_length = 0
		
		# Get CPU info
		cpu_type       = b2i(self.read_exactly(1))
		cpu_sub_type   = b2i(self.read_exactly(2))
		actual_length += 3
		
		# Get features (a.k.a. peripherals)
		feature_count  = b2i(self.read_exactly(1))
		actual_length += 1
		
		features = []
		for feature_num in range(feature_count):
			feature_id     = b2i(self.read_exactly(1))
			feature_sub_id = b2i(self.read_exactly(2))
			actual_length += 3
			
			features.append((feature_id, feature_sub_id))
		
		# Get memory segments
		segment_count  = b2i(self.read_exactly(1))
		actual_length += 1
		
		segments = []
		for segment_num in range(segment_count):
			segment_addr   = b2i(self.read_exactly(4))
			segment_length = b2i(self.read_exactly(4))
			actual_length += 8
			
			segments.append((segment_addr, segment_length))
		
		
		# Check message length was correct
		if msg_length != actual_length:
			raise MalformedResponseError("Got message of length %d, expected %d."%(
			                             actual_length, msg_length))
		
		return ((cpu_type, cpu_sub_type), features, segments)
	
	
	def reset(self):
		"""
		Reset the device.
		"""
		
		self.write(byte(BackEnd.RESET))
		self.flush()
	
	
	def periph_get_status(self, num):
		"""
		Get the status of a peripheral (feature)
		"""
		self.write(byte(BackEnd.PERIPH_GET_STATUS))
		self.write(byte(num))
		self.flush()
		
		return b2i(self.read_exactly(4))
	
	
	def periph_set_status(self, num, status):
		"""
		Set the status of a peripheral (feature)
		"""
		self.write(byte(BackEnd.PERIPH_SET_STATUS))
		self.write(byte(num))
		self.write(word(status))
		self.flush()
	
	
	def periph_send_message(self, num, message):
		"""
		Send a message to a peripheral. Returns the number of bytes accepted.
		"""
		assert(len(message) <= 255)
		
		self.write(byte(BackEnd.PERIPH_SEND_MESSAGE))
		self.write(byte(num))
		self.write(byte(len(message)))
		self.write(message)
		self.flush()
		
		return b2i(self.read_exactly(1))
	
	
	def periph_get_message(self, num, max_length = 255):
		"""
		Get a message from a peripheral of up to max_length bytes. Returns the
		message received.
		"""
		self.write(byte(BackEnd.PERIPH_GET_MESSAGE))
		self.write(byte(num))
		self.write(byte(max_length))
		self.flush()
		
		length  = b2i(self.read_exactly(1))
		message = self.read_exactly(length)
		
		if length > max_length:
			raise PeriphMessageOverflow("Expected length <= %d, got %d"%(
			                            max_length, length))
		
		return message
	
	
	def periph_download_header(self, num, length):
		"""
		Sends a header to the peripheral indicating how long (in bytes) the sequence
		of packets about to be sent is. Raises a PeriphDownloadError if not
		accepted.
		"""
		self.write(byte(BackEnd.PERIPH_DOWNLOAD_HEADER))
		self.write(byte(num))
		self.write(word(length))
		self.flush()
		
		response = self.read_exactly(1)
		
		if response == "A":
			return
		elif response == "N":
			raise PeriphDownloadError("Header requesting length %d rejected."%length)
		else:
			raise MalformedResponseError("Expected 'A' or 'N', got '%s'"%response)
	
	
	def periph_download_packet(self, num, data):
		"""
		Sends a packet of data to the peripheral. Raises a PeriphDownloadError if
		not accepted. The total length of the data sent should eventually total the
		amount originally specified in the header.
		"""
		assert(len(data) <= 255)
		
		self.write(byte(BackEnd.PERIPH_DOWNLOAD_PACKET))
		self.write(byte(num))
		self.write(byte(len(data)))
		self.write(data)
		self.flush()
		
		response = self.read_exactly(1)
		
		if response == "A":
			return
		elif response == "N":
			raise PeriphDownloadError("Packet %s of length %d rejected."%(
			                          repr(data), len(data)))
		else:
			raise MalformedResponseError("Expected 'A' or 'N', got '%s'"%response)
	
	
	def get_status(self):
		"""
		Get the status of the board. Returns a tuple
		(status, steps_remaining, steps_since_reset).
		"""
		self.write(byte(BackEnd.GET_STATUS))
		self.flush()
		
		status            = b2i(self.read_exactly(1))
		steps_remaining   = b2i(self.read_exactly(4))
		steps_since_reset = b2i(self.read_exactly(4))
		
		return (status, steps_remaining, steps_since_reset)
	
	
	def stop_execution(self):
		"""
		Stop the processor.
		"""
		self.write(byte(BackEnd.STOP_EXECUTION))
		self.flush()
	
	
	def pause_execution(self):
		"""
		Pause the processor without resetting the steps-remaining counter.
		"""
		self.write(byte(BackEnd.PAUSE_EXECUTION))
		self.flush()
	
	
	def continue_execution(self):
		"""
		Start the processor running for however many steps remain.
		"""
		self.write(byte(BackEnd.CONTINUE_EXECUTION))
		self.flush()
	
	
	def set_runtime_flags(self, flags):
		raise NotImplementedError("RTF not currently supported.")
	
	
	def get_runtime_flags(self):
		raise NotImplementedError("RTF not currently supported.")
	
	
	def trap_define(self, trap_type, num,
	                sizes,
	                addr_a, addr_b,
	                data_a, data_b,
	                in_user = True, in_priviledged = False,
	                on_read = True, on_write = True, 
	                addr_condition = None,
	                data_condition = None):
		"""
		Define a new trap with the given sizes and address/data ranges/masks and the
		specified conditions.
		"""
		assert(0 <= num < 32)
		addr_condition = addr_condition or BackEnd.CONDITION_IN_RANGE
		data_condition = data_condition or BackEnd.CONDITION_IN_RANGE
		
		self.write(byte(BackEnd.TRAP_DEFINE | trap_type))
		self.write(byte(num))
		
		# Trap condition field
		conditions  = 0
		conditions |= int(bool(bool(in_user)))        << 7
		conditions |= int(bool(bool(in_priviledged))) << 6
		conditions |= int(bool(bool(on_read)))        << 5
		conditions |= int(bool(bool(on_write)))       << 4
		conditions |= addr_condition                  << 2
		conditions |= data_condition                  << 0
		self.write(byte(conditions))
		
		self.write(byte(sizes))
		
		self.write(word(addr_a))
		self.write(word(addr_b))
		
		self.write(word(data_a))
		self.write(word(data_b))
		
		self.flush()
	
	
	def trap_read(self, trap_type, num):
		"""
		Read a trap's definition returning a dict with the same elements as the
		arguments to trap_define so that the following is a nop.
		
		  trap_define(BackEnd.TRAP_WATCHPOINT, 0, **trap_read(BackEnd.TRAP_WATCHPOINT, 0))
		"""
		assert(0 <= num < 32)
		
		self.write(byte(BackEnd.TRAP_READ | trap_type))
		self.write(byte(num))
		self.flush()
		
		conditions = b2i(self.read_exactly(1))
		sizes      = b2i(self.read_exactly(1))
		addr_a     = b2i(self.read_exactly(4))
		addr_b     = b2i(self.read_exactly(4))
		data_a     = b2i(self.read_exactly(4))
		data_b     = b2i(self.read_exactly(4))
		
		in_user        = bool(conditions & (1<<7))
		in_priviledged = bool(conditions & (1<<6))
		on_read        = bool(conditions & (1<<5))
		on_write       = bool(conditions & (1<<4))
		addr_condition = (conditions   & (0b11<<2)) >> 2
		data_condition = (conditions   & (0b11<<0)) >> 0
		
		return {
			"sizes":          sizes,
			"addr_a":         addr_a,
			"addr_b":         addr_b,
			"data_a":         data_a,
			"data_b":         data_b,
			"in_user":        in_user,
			"in_priviledged": in_priviledged,
			"on_read":        on_read,
			"on_write":       on_write, 
			"addr_condition": addr_condition,
			"data_condition": data_condition,
		}
	
	
	def trap_set_status(self, changes):
		"""
		Apply changes to all traps. Changes is {trap_num: op} where op is one of
		BackEnd.TRAP_NOP, TRAP_DELETE, TRAP_DEACTIVATE, TRAP_ACTIVATE.
		"""
		assert(max(changes.iterkeys()) < 32 and min(changes.iterkeys()) >= 0)
		
		# Calculate the bit-masks
		bitmasks = [0,0]
		for trap_num in range(32):
			if trap_num in changes:
				for bitmask in range(len(bitmasks)):
					bitmasks[bitmask] |= changes[trap_num][bitmask] << trap_num
		
		# Send the masks
		self.write(byte(BackEnd.TRAP_SET_STATUS))
		for bitmask in bitmasks[::-1]:
			self.write(word(bitmask))
		self.flush()
	
	
	def trap_read_status(self):
		"""
		Apply changes to all traps. Returned is {trap_num: state} where state is one of
		BackEnd.TRAP_NOT_IMPLEMENTED, TRAP_NOT_DEFINED, TRAP_INACTIVE, TRAP_ACTIVE
		"""
		# Request the masks
		self.write(byte(BackEnd.TRAP_READ_STATUS))
		self.flush()
		
		# Read the masks
		bitmasks = [b2i(self.read_exactly(4)) for _ in range(2)][::-1]
		
		# Divide into each trap
		statuses = {}
		for bit in range(32):
			statuses[bit] = tuple(int(bool(bitmasks[mask] & (1<<bit)))
			                      for mask in range(len(bitmasks)))
		
		return statuses
	
	
	def memory_write(self, memory_num, element_size, address, data):
		"""
		Write elements of size element_size to the specified memory starting at
		address for length elements. The element_size is given in bytes.
		"""
		# Only one bank is supported at present
		assert(memory_num == 0)
		
		self._memory_write(BackEnd.MEMORY_MEMORY, element_size, address, data)
	
	
	def register_write(self, element_size, address, data):
		"""
		Write elements of size element_size to the registers starting at address for
		length elements. The element_size is given in bytes.
		"""
		self._memory_write(BackEnd.MEMORY_REGISTER, element_size, address, data)
	
	
	def memory_read(self, memory_num, element_size, address, length):
		"""
		Read elements of size element_size from memory starting at address for
		length elements. The element_size is given in bytes.
		"""
		# Only one bank is supported at present
		assert(memory_num == 0)
		
		return self._memory_read(BackEnd.MEMORY_MEMORY, element_size, address, length)
	
	
	def register_read(self, element_size, address, length):
		"""
		Read elements of size element_size from registers starting at address for
		length elements. The element_size is given in bytes.
		"""
		return self._memory_read(BackEnd.MEMORY_REGISTER, element_size, address, length)
	
	
	def _memory_write(self, memory_type, element_size, address, data):
		"""
		Internal Use: reg/mem writing function. Will presumably be replaced if/when
		multiple memory support is added.
		
		Write elements of size element_size to memory/registers starting at address
		for length elements. The element_size is given in bytes. The memory type is
		one of BackEnd.MEMORY_MEMORY or MEMORY_REGISTER.
		"""
		length = (len(data) / element_size)
		assert(element_size in (1, 2, 4, 8))
		assert(length < (1<<16))
		
		element_size_field = {
			1 : 0b000,
			2 : 0b001,
			4 : 0b010,
			8 : 0b011,
		}[element_size]
		
		self.write(byte(BackEnd.MEMORY_WRITE | memory_type | element_size_field))
		self.write(word(address))
		self.write(half(length))
		self.write(data)
		self.flush()
	
	
	def _memory_read(self, memory_type, element_size, address, length):
		"""
		Internal Use: reg/mem writing function. Will presumably be replaced if/when
		multiple memory support is added.
		
		Read elements of size element_size from memory/registers starting at address
		for length elements. The element_size is given in bytes. The memory type is
		one of BackEnd.MEMORY_MEMORY or MEMORY_REGISTER.
		"""
		assert(element_size in (1, 2, 4, 8))
		assert(length < (1<<16))
		
		element_size_field = {
			1 : 0b000,
			2 : 0b001,
			4 : 0b010,
			8 : 0b011,
		}[element_size]
		
		self.write(byte(BackEnd.MEMORY_READ | memory_type | element_size_field))
		self.write(word(address))
		self.write(half(length))
		self.flush()
		
		return self.read_exactly(length * element_size)
	
	
	def periph_download(self, num, data):
		"""
		Download some data into a peripheral (aka feature).
		"""
		for _ in self.periph_download_(num, data):
			pass
	
	def periph_download_(self, num, data):
		"""
		Download some data into a peripheral (aka feature).
		Yields the amount of data sent every packet.
		"""
		assert(num >= 0)
		
		# Send the header
		self.write(byte(BackEnd.PERIPH_DOWNLOAD_HEADER))
		self.write(byte(num))
		self.write(word(len(data)))
		self.flush()
		
		# Get the ack
		resp = self.read(1)
		if resp != "A":
			raise BackEndError("Expected 'A', got %s"%(repr(resp)))
		
		# Send the data, packet by packet
		sent = 0
		while data:
			packet = data[:BackEnd.PACKET_LENGTH]
			data   = data[BackEnd.PACKET_LENGTH:]
			length = len(packet)
			sent  += length
			
			# Send a packet
			self.write(byte(BackEnd.PERIPH_DOWNLOAD_PACKET))
			self.write(byte(num))
			self.write(byte(length))
			self.write(packet)
			self.flush()
			
			resp = self.read(1)
			if resp != "A":
				raise BackEndError("Expected 'A', got %s"%(repr(resp)))
			
			yield sent
	
	
	def run(self, max_steps = 0,
	        halt_on_watchpoint = True, halt_on_breakpoint = True,
	        halt_on_mem_fault = False, step_over_swi = False,
	        step_over_bl = False, break_on_first_instruction = True):
		"""
		Start program execution for a certain number of steps.
		"""
		
		command  = BackEnd.RUN
		command |= int(bool(halt_on_watchpoint))         << 5
		command |= int(bool(halt_on_breakpoint))         << 4
		command |= int(bool(halt_on_mem_fault))          << 3
		command |= int(bool(step_over_swi))              << 2
		command |= int(bool(step_over_bl))               << 1
		command |= int(bool(break_on_first_instruction)) << 0
		
		self.write(byte(command))
		self.write(word(max_steps))
		self.flush()
