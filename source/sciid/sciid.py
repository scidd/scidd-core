
from abc import abstractproperty

import sciid
from . import exc
#from . import astro

class SciID:
	'''
	This class is wrapper around SciID identifiers.

	:param sciid: the SciID identifier
	'''
	def __init__(self, id_:str=None, resolver=None):
		print("sciid init")
		if id_ is None:
			raise ValueError("An identifier must be provided.")
		self.sciid = id_
		# note: only minimal validation is being performed
		if self.is_valid is False:
			raise ValueError("The provided identifier was not validated as a valid SciID.")
			
		# set the resolver
		# if resolver is None:
		# 	raise exc.ValidResolverNotFound("A valid resolver for this SciID was not specified or else a default resolver not provided.")
	
	def __new__(cls, id_:str=None, resolver=None):
		'''
		SciID is a factory class; if the prefix is identified as having a subclass dedicated to it, that subclass is instantiated.
		'''
		if cls is SciID:
			if id_.startswith("sciid:/astro/data/"):
				return super().__new__(sciid.astro.SciIDAstroData)
			elif id_.startswith("sciid:/astro/file/"):
				return super().__new__(sciid.astro.SciIDAstroFile)
		return super().__new__(cls)

	def __str__(self):
		# this is useful so one can use str(s), and "s" can be either a string or SciID object.
		return self.sciid
	
	def __repr__(self):
		return "<{0}.{1} object at {2} '{3}'>".format(self.__class__.__module__, self.__class__.__name__, hex(id(self)), self.sciid)
	
	@abstractproperty
	def is_valid(self) -> bool:
		'''
		Performs basic validation of the syntax of the identifier
		
		This method performs minimal validation; subclasses are expected to
		perform more rigorous checks.
		:returns: True if this generally looks like an identifier, False if not
		'''
		# sometimes it might be beneficial for overriding classes to call super, other times it's inefficient and redundant.
		return self.sciid.startswith("sciid:/")
	
	@abstractproperty
	def is_file(self) -> bool:
		# note: this may not be an easily determined property, but let's assume for now it is
		# todo: what to return if indeterminate?
		''' Returns 'True' if this identifier points to a file. '''
		pass

	@abstractproperty
	def url(self) -> str:
		'''
		
		'''
		if self.resolver is None:
			raise exc.NoResolverAssignedException("Attempting to resolve a SciID without having first set a resolver object.")
