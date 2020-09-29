

from abc import ABC, abstractmethod

class Resolver(ABC):
	'''
	This class resolves SciDDs into URLs that point to the resource.
	
	This is an abstract base class to be used to create domain-specific resolvers from.
	The core SciDD package does not provide a resolver.
	'''
	_default_instance = None
	
	def __init__(self, scheme:str='https', host:str=None, port:int=None):
		self.scheme = scheme
		self.host = host
		self.port = port
		self._base_url = None
				
	def __repr__(self):
		return "<{} object at {} '{}://{}:{}'>".format(self.__class__.__name__, hex(id(self)), self.scheme, self.host, self.port)

	@property
	def base_url(self):
		'''
		Returns the base URL (i.e. without a path) used to resolve SciDDs, e.g. ``https://apihost:port``.
		'''
		if self._base_url is None:
			if self.port is None:
				if self.scheme == "https":
					port = 443
				else:
					port = 80
					self._base_url = f"{scheme}://{self.host}"
			else:
				if (self.scheme == "https" and self.port == 443) or (self.scheme == "http" and self.port == 80):
					self._base_url = f"{self.scheme}://{self.host}"
				else:
					self._base_url = f"{self.scheme}://{self.host}:{self.port}"
		return self._base_url
		
	@classmethod
	def default_resolver(cls):
		'''
		This method returns a default resolver that is preconfigured with default values designed to be used out of the box (batteries included).
		
		The implementation is expected to be located in subclasses of this class.
		'''
		pass # subclass to implement
		
	@abstractmethod
	def urlForSciDD(self, scidd) -> str:
		'''
		This method resolves a SciDD into a URL that can be used to retrieve the resource.
		'''
		pass # subclass to implement
				
	@abstractmethod
	def resourceForID(self, scidd):
		'''
		Resolve the provided ``scidd:`` identifier and retrieve the resource it points to.
		'''
		pass # subclass to implement