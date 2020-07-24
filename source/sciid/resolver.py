
from abc import abstractmethod

class Resolver:
	'''
	This class resolves SciIDs into URLs that point to the resource.
	'''
	_default_instance = None
	
	def __init__(self, scheme:str='https', host:str=None, port:int=None):
		self.scheme = scheme
		self.host = host
		self.port = port
		
	def __repr__(self):
		return "<{} object at {} '{}://{}:{}'>".format(self.__class__.__name__, hex(id(self)), self.scheme, self.host, self.port)

	@property
	def base_url(self):
		if self.port is None:
			if self.scheme == "https":
				port = 443
			else:
				port = 80
			return f"{scheme}://{self.host}"
		else:
			if (self.scheme == "https" and self.port == 443) or (self.scheme == "http" and self.port == 80):
				return f"{self.scheme}://{self.host}"
			else:
				return f"{self.scheme}://{self.host}:{self.port}"
	
	@classmethod
	def default_resolver(cls):
		'''
		This method returns a default resolver that is pre-preconfigured with default values designed to be used out of the box (batteries included).
		
		The implementation is expected to be located in subclasses of this class.
		'''
		pass
		
	@abstractmethod
	def url_for_sciid(self, sciid) -> str:
		'''
		This method resolves a SciID into a URL that can be used to retrieve the resource.
		'''
		pass # subclass to implement
				
	@abstractmethod
	def resource_for_id(self, sciid):
		'''
		Resolve the provided "sciid:" identifier and retrieve the resource it points to.
		'''
		pass # subclass to implement