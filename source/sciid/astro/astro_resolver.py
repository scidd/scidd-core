
import os

from .. import Resolver

class SciIDResolverAstro(Resolver):
	'''
	
	'''
	
	def __init__(self, scheme:str="https", host:str=None, port:int=None):
		super().__init__(scheme=scheme, host=host, port=port)
	
	@classmethod
	def default_resolver(cls):
		'''
		This method returns a default resolver that is pre-preconfigured with default values designed to be used out of the box (batteries included).
		
		The same object will always be returned from this method (pseudo-singleton).
		'''
		if cls._default_instance is None:
			if "SCIID_ASTRO_RESOLVER_HOST" in os.environ:
				host = os.environ["SCIID_ASTRO_RESOLVER_HOST"]
			else:
				host = "api.trillianverse.org"
			
			if "SCIID_ASTRO_RESOLVER_PORT" in os.environ:
				port = os.environ["SCIID_ASTRO_RESOLVER_PORT"]
			else:
				port = 443
			cls._default_instance = cls(host=host, port=port)
		return cls._default_instance
	
	def url_for_sciid(self, sciid) -> str:
		'''
		This method resolves a SciID into a URL that can be used to retrieve the resource.
		'''
		# strip leading identifier text:
		sciid = self.sciid[len("sciid:/astro"):]
		
		url = sciid
		return url
		
		