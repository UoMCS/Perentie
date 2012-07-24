#!/usr/bin/env python

"""
Exceptions raised by the protocol.
"""


class BackEndError(Exception):
	pass


class ReadError(BackEndError):
	pass


class MalformedResponseError(BackEndError):
	pass


class MalformedPingResponseException(MalformedResponseError):
	def __init__(self, response):
		MalformedResponseError.__init__(self, "Expected OK??, got '%s'"%repr(response))
		self.response = response


class PeriphMessageOverflow(BackEndError):
	pass


class PeriphDownloadError(BackEndError):
	pass

