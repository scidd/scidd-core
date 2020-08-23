
import io
import os
import re
import pdb
import json
import pathlib
from typing import Union, List

import sciid
from sciid import LocalAPICache
import astropy.units as u
from astropy.coordinates import SkyCoord

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
		if isinstance(sci_id, SciID):
			sci_id = str(sci_id)
		if not sci_id.startswith("sciid:/astro/") and sci_id.startswith("/"):
			# allow abbreviated form, e.g. "/data/galex/..." becomes "sciid:/astro/galex/...";
			sci_id = "sciid:/astro" + sci_id
		if resolver is None:
			resolver = SciIDResolverAstro.default_resolver()
		
		super().__init__(sci_id=sci_id, resolver=resolver)
		
		self._dataset = None # cache value -> this is in the form "dataset.release", e.g. "sdss.dr13"
		
	def __new__(cls, sci_id:str=None, resolver:Resolver=None):
		'''
		If the SciID passed into the constructor can be identified as being handled by a specialized subclass, that subclass is instantiated.
		'''
		if cls is SciIDAstro:
			# note: the walrus operation (3.8+) will be useful here

			# dataset specific classes
			match = re.search("sciid:/astro/(?P<type>data|file)/2mass/.+", str(sci_id))
			if match:
				if match.group("type") == "data":
					return super().__new__(sciid.astro.SciIDAstroData)
				else: # type == "file"
					return super().__new__(sciid.astro.dataset.twomass.SciIDAstro2MassFile)

			# anything else that can be handled by the "generic" classes
			if str(sci_id).startswith("sciid:/astro/data/"):
				return super().__new__(sciid.astro.SciIDAstroData)
			elif str(sci_id).startswith("sciid:/astro/file/"):
				return super().__new__(sciid.astro.SciIDAstroFile)

		return super().__new__(cls)
	
	def isValid(self) -> bool:
		'''
		Performs (very!) basic validation of the syntax of the identifier.
		'''
		return self._sciid.startswith("sciid:/astro")

	@property
	def dataset(self) -> str:
		'''
		Returns the short label of the dataset and the release separated by a '.'.
		
		In the context of astro data SciIDs, the dataset is the first collection and the release is the first
		subcollection/path element that follows.
		
		The short label can be used to get the dataset object, e.g. "galex" -> Dataset.from_short_name("galex")
		'''
		if self._dataset is None:
			match = re.search("^sciid:/astro/(data|file)/([^/]+)/([^/^.]+)", self.sciid)
			if match:
				self._dataset = ".".join([match.group(2), match.group(3)])
		#		match = re.search("^sciid:/astro/(data|file)/([^/]+)", self.sciid)
		#		if match:
		#			self._dataset = match.group(2)
		return self._dataset
		#return str(self.sciid).split("/")[3] # first string after "data/"
	
	# @property
	# def release(self) -> str:
	# 	'''
	# 	The release on a `sciid:/astro/(file|data)/<dataset>/`-style id is the subcollection/path immediately following the dataset.
	# 	'''
	# 	if self._release is None:
	# 		match = re.search(
	# 		
	# 	return self._release
	
	
class SciIDAstroData(SciIDAstro):
	'''
	An identifier pointing to data in the astronomy namespace ("sciid:/astro/data/").
	'''
	def __init__(self, sci_id:str=None, resolver:Resolver=None):
		if sci_id.startswith("sciid:") and not sci_id.startswith("sciid:/astro/data/"):
			raise exc.SciIDClassMismatch(f"Attempting to create {self.__class__} object with a SciID that does not begin with 'sciid:/astro/data/'; try using the 'SciID(sci_id)' factory constructor instead.")
		super().__init__(sci_id=sci_id, resolver=resolver)
	
	def isFile(self) -> bool:
		''' Returns 'True' if this identifier points to a file. '''
		return False

	def isValid(self) -> bool:
		'''
		Performs basic validation of the syntax of the identifier; a returned value of 'True' does not guarantee a resource will be found.
		'''
		return self._sciid.startswith("sciid:/astro/data/")
	
class SciIDAstroFile(SciIDAstro, SciIDFileResource):
	'''
	An identifier pointing to a file in the astronomy namespace ("sciid:/astro/file/").
	'''
	
	def __init__(self, sci_id:str=None, resolver:Resolver=None):
		SciIDAstro.__init__(self, sci_id=sci_id, resolver=resolver)
		SciIDFileResource.__init__(self)
		self._position = None
	
	# @property
	# def path_within_cache(self):
	# 	'''
	# 	The directory path within the top level SciID cache where the file would be written when downloaded, not including filename.
	# 	'''
	# 	if self._cache_path is None:
	# 		match = re.search("^/astro/file/(.+)#?", str(pathlib.Path(self.path)))
	# 		if match:
	# 			path_components = pathlib.Path(match.group(1)).parts[0:-1] # omit last part (filename)
	# 			self._cache_path = os.path.join("astro", *path_components)
	# 		else:
	# 			raise NotImplementedError()
	# 		logger.debug(f" --> {self._cache_path}")
	# 	return self._cache_path
	
	def isFile(self) -> bool:
		''' Returns 'True' if this identifier points to a file. '''
		return True

	def isValid(self) -> bool:
		'''
		Performs basic validation of the syntax of the identifier; a returned value of 'True' does not guarantee a resource will be found.
		'''
		return self._sciid.startswith("sciid:/astro/file/")

	@property
	def filenamesUniqueInDataset(self) -> bool:
		'''
		Returns true if all filenames within the dataset this identifier belongs to are unique.
		
		This is generally true so 'True' is the default. It is expected that subclasses
		override this method since handling of non-unique filenames within a dataset
		will generally require special handling anyway.
		'''
		return True 

	def uniqueIdentifierForFilename(self) -> str:
		'''
		Returns a string that can be used as a unique identifier to disambiguate files within the dataset that have the same name.
		
		The default returns an empty string as it is assumed filenames within a dataset are unique;
		override this method to return an identifier when this is not the case.		
		'''
		return ""

	@property
	def filename(self, without_compressed_extension:bool=True) -> str:
		'''
		If this identifier points to a file, return the filename, "None" otherwise.
		:param without_compressed_extension: if True, removes extensions indicating compression (e.g. ".zip", ".tgz", etc.)
		'''
		# the filename should always be the last part of the URI if this is a filename, excluding any fragment
		
		if self.isFile():
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
		Returns a specific location (URL) that points to the resource described by this SciID using the :py:class:`sciid.Resolver` assigned to this object.
		'''
		if self._url is None:
			if self.resolver is None:
				raise exc.NoResolverAssignedException("Attempting to resolve a SciID without having first set a resolver object.")
			
			self._url = self.resolver.urlForSciID(self)
		return self._url

	@classmethod
	def fromFilename(cls, filename:str, allow_multiple_results=False) -> Union[SciID,List[SciID]]:
		'''
		A factory method that attempts to return a SciID identifier from a filename alone; depends on domain-specific resolvers.
		
		:param filename: the filename to create a SciID identifier from
		:param domain: the top level domain of the resource, e.g. `astro`
		:param allow_multiple_results: when True will raise an exception if the filename is not unique; if False will always return an array of matching SciIDs.
		'''
		CACHE_KEY = f"astro/filename:{filename}"
		
		try:
			# fetch from cache
			list_of_results = json.loads(LocalAPICache.defaultCache()[CACHE_KEY])
			logger.debug("API cache hit")
		except KeyError:
			# Use the generic filename resolver which assumes the filename is unique across all curated data.
			# If this is not the case, override this method in a subclass (e.g. see the twomass.py file).
			list_of_results = SciIDResolverAstro.default_resolver().genericFilenameResolver(filename=filename)
			
			# save to cache
			try:
				LocalAPICache.defaultCache()[CACHE_KEY] = json.dumps(list_of_results)
			except Exception as e:
				raise e # remove after debugging
				logger.debug(f"Note: exception in trying to save API response to cache: {e}")
				pass

		if allow_multiple_results:
			for record in list_of_results:
				s = SciID(rec["sciid"])
				s.url = rec["url"] # since we have it here anyway
				s._uncompressed_file_size = rec["file_size"]
				s._dataset = ".".join([rec["dataset"], rec["release"]]) # note there isn't a public interface for this
			return [SciID(rec["sciid"]) for rec in list_of_results]
		else:
			if len(list_of_results) == 1:
				return SciID(list_of_results[0]["sciid"])
			elif len(list_of_results) > 1:
				raise exc.UnableToResolveFilenameToSciID(f"Multiple SciIDs were found for the filename '{filename}'. Set the flag 'allow_multiple_results' to True to return all in a list.")
			else:
				raise exc.UnableToResolveFilenameToSciID(f"Could not find the filename '{filename}' in known datasets. Is the dataset one of those currently implemented?")
				# TODO: create API call to list currently implemented datasets

	@property
	def position(self) -> SkyCoord:
		'''
		Returns a representative sky position for this file; this value should not be used for science.
		
		A file could contain data that points one or more (even hundreds of thousands) locations on the sky.
		This method effective returns the first location found, e.g. the sky location of the reference pixel
		from the first image HDU, reading the first WCS from the file, reading known keywords, etc.
		It is intended to be used as an identifier to place the file *somewhere* on the sky, but it is not
		intended to be exhaustive. Use traditional methods to get positions for analysis. Whenever possible
		(but not guaranteed), the value returned is in J2000 IRCS.
		'''
		if self._position is None:
			# note that the API automatically discards file compression extensions
			parameters = {
				"filename" : self.filename,
				"dataset" : self.dataset
			}
	
			# handle cases where filenames are not unique
			if self == "2mass":
				raise NotImplementedError("TODO: handle 'uniqueid' or whatever we land on to disambuguate filenames.")
				parameters[""] = None
	
			records = sciid.API().get(path="/astro/data/filename-search", params=parameters)
			
			logger.debug(records)
			if not len(records) == 1:
				raise Exception(f"Expected to find a single matching record; {len(records)} found.")
				
			pos = records[0]["position"] # array of two points
			self._position = SkyCoord(ra=pos[0]*u.deg, dec=pos[1]*u.deg)
			
			# while we have the info...
			if self._url is None:
				self._url = records[0]["url"]
				self._uncompressed_file_size = records[0]["file_size"]
			
		return self._position
		