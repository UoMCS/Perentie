#!/usr/bin/env python

"""
System model package.
"""


from system_stump import StumpSystem
from system_mu0   import MU0System


def get_model(cpu, cpu_subtype):
	"""
	Get the model associated with the provided cpu and cpu_subtype.
	"""
	
	return {
		2: StumpSystem,
		3: MU0System,
	}[cpu]()
