
import io
import os
import re
import pdb
import pathlib

import sciid
from .. import exc
from ..logger import sciid_logger as logger
from .. import SciID, SciIDFileResource, Resolver
from . import SciIDResolverAstro

compression_extensions = [".zip", ".tgz", ".gz", "bz2"]

class SciIDAstro(SciID):
	'''
	This class is wrapper around SciID identifiers in the 'astro' namespace ("sciid:/astro").
	
	:param sciid: a SciID identifier or one assumed to have "sciid:/astro" prepended to it
	:param resolver: an object that can resolve the identifier to a URL; for most cases using the default resolver by passing 'None' is the right choice
	'''
	def __init__(self, sci_id:str=None, resolver:Resolver=None):
		if not sci_id.startswith("sciid:/astro/") and sci_id.startswith("/"):
			# allow abbreviated form
			sci_id = "sciid:/astro" + sci_id
		if resolver is None:
			resolver = SciIDResolverAstro.default_resolver()
		
		super().__init__(sci_id=sci_id, resolver=resolver)
		
		self._dataset = None # cache value
		
	def __new__(cls, sci_id:str=None, resolver:Resolver=None):
		'''
		If the SciID passed into the constructor can be identified as being handled by a specialized subclass, that subclass is instantiated.
		'''
		if cls is SciIDAstro:
			if sci_id.startswith("sciid:/astro/data/"):
				return super().__new__(sciid.astro.SciIDAstroData)
			elif sci_id.startswith("sciid:/astro/file/"):
				return super().__new__(sciid.astro.SciIDAstroFile)
		return super().__new__(cls)
	
	@property
	def is_valid(self):
		'''
		Performs basic validation of the syntax of the identifier
		'''
		return self.sciid.startswith("sciid:/astro")

	@property
	def dataset(self) -> str:
		'''
		Returns the short label of the dataset; in the context of astro data SciIDs, the dataset is the first collection.
		
		The short label can be used to get the dataset object, e.g. "galex" -> Dataset.from_short_name("galex")
		'''
		if self._dataset is None:
			match = re.search("^sciid:/astro/(data|file)/([^/]+)", self.sciid)
			if match:
				self._dataset = match.group(2)
		return self._dataset
#		return str(self.sciid).split("/")[3] # first string after "data/"
	
class SciIDAstroData(SciIDAstro):
	'''
	An identifier pointing to data in the astronomy namespace ("sciid:/astro/data/").
	'''
	def __init__(self, sci_id:str=None, resolver:Resolver=None):
		if sci_id.startswith("sciid:") and not sci_id.startswith("sciid:/astro/data/"):
			raise exc.SciIDClassMismatch(f"Attempting to create {self.__class__} object with a SciID that does not begin with 'sciid:/astro/data/'; try using the 'SciID(sci_id)' factory constructor instead.")
		super().__init__(sci_id=sci_id, resolver=resolver)
	
	def is_file(self) -> bool:
		''' Returns 'True' if this identifier points to a file. '''
		return False

	def is_valid_id(self) -> bool:
		'''
		Performs basic validation of the syntax of the identifier; a returned value of 'True' does not guarantee a resource will be found.
		'''
		return self.sciid.startswith("sciid:/astro/data/")
	
class SciIDAstroFile(SciIDAstro, SciIDFileResource):
	'''
	An identifier pointing to a file in the astronomy namespace ("sciid:/astro/file/").
	'''
	
	def __init__(self, sci_id:str=None, resolver:Resolver=None):
		SciIDAstro.__init__(self, sci_id=sci_id, resolver=resolver)
		SciIDFileResource.__init__(self)
	
	@property
	def path_within_cache(self):
		'''
		The directory path within the top level SciID cache where the file would be written when downloaded, not including filename.
		'''
		if self._cache_path is None:
			match = re.search("^/astro/file/(.+)#?", str(pathlib.Path(self.path)))
			if match:
				path_components = pathlib.Path(match.group(1)).parts[0:-1] # omit last part (filename)
				self._cache_path = os.path.join("astro", *path_components)
			else:
				raise NotImplementedError()
			logger.debug(f" --> {self._cache_path}")
		return self._cache_path
	
	def is_file(self) -> bool:
		''' Returns 'True' if this identifier points to a file. '''
		return True

	def is_valid_id(self) -> bool:
		'''
		Performs basic validation of the syntax of the identifier; a returned value of 'True' does not guarantee a resource will be found.
		'''
		return self.sciid.startswith("sciid:/astro/file/")

	@property
	def filename(self, without_compressed_extension:bool=True) -> str:
		'''
		If this identifier points to a file, return the filename, "None" otherwise.
		:param without_compressed_extension: if True, removes extensions indicating compression (e.g. ".zip", ".tgz", etc.)
		'''
		# the filename should always be the last part of the URI if this is a filename, excluding any fragment
		
		if self.is_file:
			uri = self.sciid.split("#")[0]     # strip fragment identifier (if present)
			filename = uri.split("/")[-1] # filename will always be the last element
			
			if without_compressed_extension:
				fname, ext = os.path.splitext(filename)
				if ext in compression_extensions:
					filename = fname
			return filename
		else:
			return None
			
	@property
	def url(self) -> str:
		'''
		Returns a specific location (URL) that points to the resource described by this SciID using the `sciid.Resolver` assigned to this object.
		'''
		if self._url is None:
			if self.resolver is None:
				raise exc.NoResolverAssignedException("Attempting to resolve a SciID without having first set a resolver object.")
			
			self._url = self.resolver.url_for_sciid(self)
		return self._url

