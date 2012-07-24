#!/usr/bin/env python

"""
Definitions of the various architectures that can be debugged.
"""


from stump import STUMP
from mu0   import MU0


def get_model(cpu, cpu_subtype):
	"""
	Get the definition associated with the provided cpu and cpu_subtype.
	"""
	
	return {
		2: STUMP,
		3: MU0,
	}[cpu]()
