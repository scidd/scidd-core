
from __future__ import annotations # remove in Python 4.0
# Needed for forward references, see:
# https://stackoverflow.com/a/33533514/2712652

import io
import os
import bz2
import pdb
import gzip
import shutil
import pathlib
from typing import Union
from zipfile import ZipFile
from abc import ABC, abstractproperty, abstractmethod

import astropy
import requests

import sciid
from . import exc
from .cache import SciIDCacheManager, SciIDCacheManagerBase
from .resolver import Resolver
from .logger import sciid_logger as logger

# list of file extensions that we treat as compressed files
COMPRESSED_FILE_EXTENSIONS = [".gz", ".bz2", ".zip"]

class SciID(): #, metaclass=SciIDMetaclass):
	'''
	This class is wrapper around SciID identifiers.

	:param sci_id: the SciID identifier
	'''
	def __init__(self, sci_id:str=None, resolver=None):
		if sci_id is None:
			raise ValueError("An identifier must be provided.")
		if isinstance(sci_id, dict):
			raise ValueError("The 'sci_id' value should be a string, not a dictionary. Maybe you forgot to extract the value from an API result?")
		self._sciid = sci_id # string representation of the identifier
		self.resolver = resolver
		self._url = None # a place to cache a URL once the record has been resolved
		
		# note: only minimal validation is being performed
		if self.isValid() is False:
			raise ValueError("The provided identifier was not validated as a valid SciID.")
			
		# set the resolver
		# if resolver is None:
		# 	raise exc.ValidResolverNotFound("A valid resolver for this SciID was not specified or else a default resolver not provided.")
	
	def __new__(cls, sci_id:str=None, resolver=None):
		'''
		SciID is a factory class; if the prefix is identified as having a subclass dedicated to it, that subclass is instantiated.
		'''
		# Useful ref: https://stackoverflow.com/a/5953974/2712652
		if cls is SciID:
			if str(sci_id).startswith("sciid:/astro"):
				from sciid.astro import SciIDAstro, SciIDAstroFile
				if "/file/" in str(sci_id):
					return SciIDAstroFile.__new__(SciIDAstroFile, sci_id=sci_id, resolver=resolver)
				else:
					return SciIDAstro.__new__(SciIDAstro, sci_id=sci_id, resolver=resolver)
			# if sci_id.startswith("sciid:/astro/data/"):
			# 	return super().__new__(sciid.astro.SciIDAstroData)
			# elif sci_id.startswith("sciid:/astro/file/"):
			# 	return super().__new__(sciid.astro.SciIDAstroFile)
		return super().__new__(cls)

	def __str__(self):
		# this is useful so one can use str(s), and "s" can be either a string or SciID object.
		return self._sciid
	
	def __repr__(self):
		return "<{0}.{1} object at {2} '{3}'>".format(self.__class__.__module__, self.__class__.__name__, hex(id(self)), self._sciid)
	
	@property
	def sciid(self) -> str:
		''' Returns a string representation of the identifier. '''
		return self._sciid
	
	@sciid.setter
	def sciid(self, new_id):
		if not isinstance(new_id, str):
			raise ValueError("The 'sciid' property must be a string.")
		self._sciid = new_id
	
	def isValid(self) -> bool:
		'''
		Performs (very) basic validation of the syntax of the identifier
		
		This method performs minimal validation; subclasses are expected to
		perform more rigorous but not necessarily exhaustive checks.
		
		:returns: ``True`` if this generally looks like an identifier, ``False`` if not
		'''
		# sometimes it might be beneficial for overriding classes to call super, other times it's inefficient and redundant.
		return self.sciid.startswith("sciid:/")
	
	def isFile(self) -> bool:
		# note: this may not be an easily determined property, but let's assume for now it is
		# todo: what to return if indeterminate?
		''' Returns ``True`` if this identifier points to a file. '''
		pass

	@property
	def url(self) -> str:
		'''
		Returns a URL that can be used to retrieve the resource described by this object using the previously set resolver.
		'''
		if self._url is None:
			if self.resolver is None:
				raise exc.NoResolverAssignedException("Attempting to resolve a SciID without having first set a resolver object.")
		
			self._url = self.resolver.urlForSciID(self)

		return self._url

	@url.setter
	def url(self, new_value):
		self._url = new_value

	@property
	def path(self) -> str:
		'''
		Returns the SciID as a string without the scheme prefix (i.e. the ``sciid:`` prefix is removed).
		'''
		return str(self).replace('sciid:', '')
	
	@property
	def fragment(self) -> str:
		'''
		The fragment part of the SciID; this component of the string identifies data within the resource.
		'''
		if "#" in self._sciid:
			return self._sciid.split("#")[1]
		else:
			return None
	
	@property
	def metadata(self) -> dict:
		'''
		Returns metadata of this file as a dictionary. [Format to be determined.]
		'''
		raise NotImplementedError()
		
	@classmethod
	def fromFilename(cls, filename:str, domain:str, allow_multiple_results=False) -> SciID:
		'''
		A factory method that attempts to return a SciID identifier from a filename alone; depends on domain-specific resolvers.
		
		:param filename: the filename to create a SciID identifier from
		:param domain: the top level domain of the resource, e.g. ``astro``: todo: create a .sciid.conf file with a default domain setting
		:param allow_multiple_results: when True will raise an exception the filename is not unique; if False will always return an array of matching SciIDs.
		'''
		if filename is None or len(filename) == 0:
			raise ValueError("A filename must be provided.")
		if domain == "astro":
			from sciid.astro import SciIDAstroFile
			#return SciIDAstroFile.__new__(SciIDAstro, sci_id=sci_id, resolver=resolver)
			# .. todo: check here if the path looks like a file in the first place
			return SciIDAstroFile.fromFilename(filename=filename, allow_multiple_results=allow_multiple_results)
		else:
			raise NotImplementedError(f"The top level domain '{domain}' is not currently implemented (the only domain currently implemented is 'astro'.")

class SciIDFileResource:
	'''
	This class represents a :class:`SciID` identifier that specifically points to and helps manage a file resource.
	
	It provides additional properties, methods, and utility that is useful for working with files.
	'''
	
	# Class variables
	# ---------------
	# Use this cache manager for all new SciIDs (that point to files, of course).
	# Note that this is a class variable! Changing it will not change any
	# previously set cache manager on existing SciIDFileResource objects.
	_default_cache_manager = SciIDCacheManager.default_cache()
	
	def __init__(self):
		self._filepath = None # store local location
		self._filename = None # cache the filename derived from the identifier
		self.read_only_caches = list() # list of SciIDCacheManager objects that point to read-only caches
		self._filename_unique_identifier = None # a string used to disambiguate files with the same name in the same dataset release

		if __class__._default_cache_manager is None:
			self.cache = SciIDCacheManager.default_cache()
		else:
			self.cache = __class__._default_cache_manager
			
		# information retrieved from the Trillian API, used to test successful download of file, todo: can also use hash but will be slower
		self._uncompressed_file_size = None
		
		# Caches
		# A SciID is an "abstract" representation of the data. A file (in this case) can be located
		# in multiple caches managed by the same program. The dictionary below stores the path
		# location within each cache it encounters (i.e. relative to the top level of the cache).
		# The value is not calculated here.
		self._path_within_cache = dict() # key=cache manager obj, value=path; save value per cache object for repeated lookups
		
	# @property
	# def filename_without_compression_extension(self):
	# 	'''
	# 	The filename after removing any extensions related to compression (e.g. '.zip', '.bz2', '.gz').
	# 	'''
	# 	filename = self.filename
	# 	for ext in COMPRESSED_FILE_EXTENSIONS:
	# 		if filename.endswith(ext)
	# 			return filename[:-len(ext)]
	# 	return filename
	
	@property
	def filename(self) -> str:
		'''
		The filename the identifier points to. Note that it is not guaranteed to be unique across all identifiers.
		
		The filename is the last component of the identifier once the query, fragment, and xxx components are removed from the identifier.
		For example, given this identifier:
		
		.. code-block::
		
		    sciid:/astro/data/2mass/allsky/hi0550232.fits;uniqueid=20000116.n.55?a=b
		
		The optional ``;uniqueid=20000116.n.55`` fragment is not part of the filename and is delineated by the ``;`` character.
		The optional query component ``a=b`` is delineated by the first ``?``.
		Removing both and returning the final path component yields the filename.
		'''
		if self._filename is None:
			path = self.path # remove scheme
			path = path.split(";")[0] # remove scheme-specific segment
			self._filename = os.path.filenam(path)
		return self._filename
	
	@property
	def filepath(self) -> pathlib.Path:
		'''
		Return local file path for resource, including the filename; download if needed.
		
		Note: Using autocomplete in an interactive environment (e.g. Jupyter notebook, iPython)
		on a SciID object will cause the associated file to be downloaded if it's not found on disk.
		'''
		# Note: this isn't 
		if self._filepath is None:
			# already in cache?
			expected_filepath = self.cache.path / self.pathWithinCache / self.filename
			if expected_filepath.exists():
				self._filepath = expected_filepath
				#logger.debug(f'Found in cache: "{expected_filepath}"')
			else:
				# file not there, download
				#logger.debug(f" -----> {self.cache.path / self.pathWithinCache}")
				self.downloadTo(path=self.cache.path / self.pathWithinCache)
				
				# check again
				if expected_filepath.exists():
					self._filepath = expected_filepath
				else:
					raise NotImplementedError()
					
				self._filepath = expected_filepath

		return self._filepath
	
	@property
	def fileExtension(self) -> str:
		'''
		Return the file extension, if there is one.
		'''
		return os.splitext(self.filename)[1]
	
	@property
	def pathWithinCache(self) -> pathlib.Path:
		'''
		Returns the path where this file should be located for the currently set cache manager (``self.cache``).
		'''
		try:
			return self._path_within_cache[self.cache]
		except KeyError:
			path = self.cache.pathWithinCache(sci_id=self)
			self._path_within_cache[self.cache] = path
			assert not str(path).startswith("/"), "This causes problems when joining paths."
			return path
	
	def isInCache(self) -> bool:
		'''
		Check if the resource is available locally, useful if one does not want to download it automatically.
		
		This method will look for zero-length files (e.g. if there was a previous error or code interrupted).
		In this case, the file will be deleted and ``False`` will be returned.
		'''
		# If the file is found, sets self._filepath if not already set.
		full_path = self.cache.path / self.pathWithinCache / self.filename
		if full_path.exists():
			if full_path.stat().st_size == 0:
				# possible error in earlier run
				full_path.unlink(missing_ok=True) # delete zero length file (won't be missing here!)
				return False
			return True
		else:
			return False
	
	@property
	def uncompressedSize(self) -> astropy.units.quantity.Quantity:
		'''
		Returns the known uncompressed size of this file. This is retrieved from a database, not measured on disk, so may return ``None``.
		'''
		# This is not a property that can be determined offline. If any query is made that contains it, it should be set there.
		return self._uncompressed_file_size
	
	def downloadTo(self, path:Union[pathlib.Path,str]=None) -> pathlib.Path:
		'''
		Download the resource to the specified directory. It will be decompressed if it’s compressed from the source.
		
		:param path: the path to download the file to; does not include the filename
		:returns: the full :py:attr:`filepath` to the file that is downloaded
		'''		
		logger.debug(f"downloading to: '{path}'")
		if path is None:
			path = self.cache.path / self.pathWithinCache
		elif isinstance(path, str):
			path = pathlib.Path(path)
		
		if self.isInCache(): # checks for zero length file; if found, deletes and returns False
			return
		
		if os.path.lexists(path):
			# lexists returns True for broken symbolic links;
			# useful to avoid attempting to create a directory on top of a broken link (which will crash)
			
			# is this a broken link?
			if path.exists() is False:
				raise Exception(f"Tried to set up cache but found what appears to be a broken symbolic link: '{path}'")
		else:
			path.mkdir(parents=True)
			
		url = self.url
		ext = os.path.splitext(url)[1].lower() # file extension
		
		if ext in COMPRESSED_FILE_EXTENSIONS:
			self._download_compressed_file(url=url, ext=ext, path=path)
		else:	
			#status = None
			# File is not compressed on the remote server.
			# Rather than read the whole thing into memory,
			# stream the data straight to a file on disk (making sure there are no errors).
			response = requests.get(url, stream=True)
			#logger.debug(f"=====> {response} , {response.status_code}")
			try:
				# raise "requests.HTTPError" exception if 400 <= status_code <= 600
				response.raise_for_status()
				#status = response.status_code
			except requests.HTTPError:
				if response.status_code == 404:
					logger.debug(f"404 File not found (url='{url}')")
			
					# File was not found. Try again with common file compression suffixes?
					for ext in COMPRESSED_FILE_EXTENSIONS:
						# where are you mr file?
						file_found = False
						if requests.head(url+ext).status_code == 200:
							url = url + ext
							file_found = True
							break # file will be handled below
					if file_found:
						logger.warning(f"The Trillian API expected a file to be located at '{url[0:-len(ext)]}'; found instead at '{url}'.")
						self._download_compressed_file(url=url, ext=ext, path=path)
						return
					else:
						logger.warning(f"No file was found as expected at '{url}'.")
						raise exc.FileResourceCouldNotBeFound(f"No file found where the Trillian API service expected to be found (even after looking for compressed versions of the file ('{url}').")

			try:
				# Ref: https://2.python-requests.org//en/latest/user/quickstart/#raw-response-content
				with open(self.cache.path / self.pathWithinCache / self.filename, mode='wb') as f:
					for chunk in response.iter_content(chunk_size=io.DEFAULT_BUFFER_SIZE):
						# chunk_size in bytes
						f.write(chunk)
			except requests.HTTPError as e:
				# .. todo:: handle different errors appropriately
				# - URL not found
				# - network error
				# - etc.
				raise NotImplementedError()
				
	def _download_compressed_file(self, url:str, ext:str, path:os.pathLike):
		'''
		Download the provided file that's compressed on the remote server.
		
		This is an internal implementation detail that should not be called outside of this class and is subject to change or removal.
		:param url: the full URL to the file to be downloaded
		:param ext: the file's extension, incuding the leading fullstop, e.g. `.gz`
		:param path: the local filesystem path to down the file into
		'''
		# File is compressed on remote server. Download and decompress.
		if ext in [".gz"]:
			self._download_gz_file(url=url, path=path)
		elif ext in [".bz2", ".bzip2"]:
			self._download_bz2_file(url=url, path=path)
		elif ext in [".zip"]:
			self._download_zip_file(url=url, path=path)
				
		
	def _download_gz_file(self, url:str=None, path:pathlib.Path=None):
		'''
		Private method that downloads a URL that points to a gzip compressed file. Resulting file is decompressed.
		'''
		assert url is not None, "A URL must be provided to download."
		response = requests.get(url=url)
		try:
			response.raise_for_status()
		except requests.HTTPError:
			if response.status_code == 404:
				# handle error
				raise NotImplementedError()
		
		ext = os.path.splitext(self.url)[1]
		#fname = self.filename[:-len(ext)]
		#logger.debug(f"fname={fname}")
		path_to_write = path / self.filename # the SciID will have the uncompressed filename
		logger.debug(f"About to write file to: {path} / {self.filename}")
		
		with open(path_to_write, 'wb') as f:
			shutil.copyfileobj(io.BytesIO(gzip.decompress(response.content)), f)
		
	def _download_bz2_file(self, url:str=None, path:pathlib.Path=None):
		'''
		Private method that downloads a URL that points to a bz2 compressed file. Resulting file is decompressed.
		'''
		assert url is not None, "A URL must be provided to download."
		response = requests.get(url=url)
		try:
			response.raise_for_status()
		except requests.HTTPError:
			if response.status_code == 404:
				# handle error
				raise NotImplementedError()
		
		#ext = os.path.splitext(self.url)[1]
		#fname = filename[:-len(ext)]
		#logger.debug(f"fname={fname}")
		path_to_write = path / self.filename # the SciID will have the uncompressed filename
		logger.debug(f"About to write file to: {path_to_write}")
		
		with open(path_to_write, 'wb') as f:
			shutil.copyfileobj(io.BytesIO(bz2.decompress(response.content)), f)
	
	def _download_zip_file(self, url:str=None, path:pathlib.Path=None):
		'''
		Private method that downloads a URL that points to a zip compressed file. Resulting file is decompressed.
		'''
		assert url is not None, "A URL must be provided to download."
		response = requests.get(url=url)
		try:
			response.raise_for_status()
		except requests.HTTPError:
			if response.status_code == 404:
				raise NotImplementedError() # handle error
				
		#ext = os.path.splitext(self.url)[1]
		#fname = filename[:-len(ext)]
		#logger.debug(f"fname={fname}")
		path_to_write = path / self.filename # the SciID will have the uncompressed filename
		logger.debug(f"About to write file to: {path_to_write}")
		
		# note: zip files can contain multiple files
		# todo(?) support extracting metadata for multiple files in a zip archive
		ZipFile.extract(member=ZipFile(file=io.BytesIO(data)), path=path)
