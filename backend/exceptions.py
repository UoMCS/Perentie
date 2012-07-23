#!/usr/bin/env python

"""
Exceptions raised by the protocol.
"""


class ProtocolException(Exception):
	pass


class ReadError(ProtocolException):
	pass


class MalformedResponseError(ProtocolException):
	pass


class MalformedPingResponseException(MalformedResponseError):
	def __init__(self, response):
		MalformedResponseError.__init__(self, "Expected OK??, got '%s'"%repr(response))
		self.response = response


class PeriphMessageOverflow(ProtocolException):
	pass


class PeriphDownloadError(ProtocolException):
	pass

