#!/usr/bin/env python

"""
A serial-port back-end for the protocol.
"""

from serial import Serial

from base import BackEnd

class SerialPortBackEnd(BackEnd):
	
	def __init__(self, port = None, baudrate = 115200,
	             read_timeout = 1.0, write_timeout = 0.1):
		"""
		Provides a serial-port back-end for the protocol. Timeouts are in seconds.
		"""
		BackEnd.__init__(self)
		
		# Start the emulator as a child-process
		self.serial = Serial(port,
		                     baudrate     = baudrate,
		                     timeout      = read_timeout,
		                     writeTimeout = write_timeout)
		
	
	
	def read(self, length):
		return self.serial.read(length)
	
	
	def write(self, data):
		self.serial.write(data)
	
	
	def flush(self):
		self.serial.flush()

