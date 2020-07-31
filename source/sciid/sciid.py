
import io
import os
import bz2
#import pdb
import gzip
import shutil
import pathlib
from typing import Union
from zipfile import ZipFile
from abc import ABC, abstractproperty, abstractmethod

import requests

import sciid
from . import exc
from .cache import SciIDCache
from .resolver import Resolver
from .logger import sciid_logger as logger

# list of file extensions that we treat as compressed files
COMPRESSED_FILE_EXTENSIONS = [".zip", ".gz", ".bz2"]

class SciID(): #, metaclass=SciIDMetaclass):
	'''
	This class is wrapper around SciID identifiers.

	:param sciid: the SciID identifier
	'''
	def __init__(self, sci_id:str=None, resolver=None):
		if sci_id is None:
			raise ValueError("An identifier must be provided.")
		self.sciid = sci_id
		self.resolver = resolver
		self._url = None # a place to cache a URL once the record has been resolved

		# note: only minimal validation is being performed
		if self.is_valid is False:
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
			if sci_id.startswith("sciid:/astro"):
				from sciid.astro import SciIDAstro
				return SciIDAstro.__new__(SciIDAstro, sci_id=sci_id, resolver=resolver)
			# if sci_id.startswith("sciid:/astro/data/"):
			# 	return super().__new__(sciid.astro.SciIDAstroData)
			# elif sci_id.startswith("sciid:/astro/file/"):
			# 	return super().__new__(sciid.astro.SciIDAstroFile)
		return super().__new__(cls)

	def __str__(self):
		# this is useful so one can use str(s), and "s" can be either a string or SciID object.
		return self.sciid
	
	def __repr__(self):
		return "<{0}.{1} object at {2} '{3}'>".format(self.__class__.__module__, self.__class__.__name__, hex(id(self)), self.sciid)
	
	@abstractproperty
	def is_valid(self) -> bool:
		'''
		Performs (very) basic validation of the syntax of the identifier
		
		This method performs minimal validation; subclasses are expected to
		perform more rigorous but not necessarily exhaustive checks.
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

	@property
	def url(self) -> str:
		'''
		Returns a URL that can be used to retrieve the resource described by this object using the previously set resolver.
		'''
		if self._url is None:
			if self.resolver is None:
				raise exc.NoResolverAssignedException("Attempting to resolve a SciID without having first set a resolver object.")
		
			self._url = self.resolver.url_for_sciid(self)

		return self._url

	@url.setter
	def url(self, new_value):
		self._url = new_value

	@property
	def path(self) -> str:
		'''
		Returns the SciID as a string without the scheme prefix (i.e. 'sciid:' removed).
		'''
		return str(self).replace('sciid:', '')
		

class SciIDFileResource:
	
	def __init__(self):
		self._filepath = None # store local location
		self.cache = SciIDCache.default_cache()
		self._cache_path = None # path to file relative to the top level cache
			
	@property
	def path_within_cache(self) -> os.PathLike:
		'''
		The directory path within the top level SciID cache where the file would be written when downloaded.
		
		This can be domain-specific, e.g. a collection that has millions of files might be better served
		with a custom scheme. It's recommended to subclass this class for such files.
		'''
		raise Exception()
		if self._cache_path is None:
			# remove prefix and leading "/"
			self._cache_path = self.path.parent
			logger.debug(f" cache_path = {self._cache_path} / {self.path}")
		return self._cache_path
	
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
	def filepath(self) -> pathlib.Path:
		'''
		Return local file path for resource, including the filename; download if needed.
		'''
		if self._filepath is None:
			# already in cache?
			expected_filepath = self.cache.path / self.path_within_cache / self.filename
			if expected_filepath.exists():
				self._filepath = expected_filepath
			else:
				# file not there, download
				logger.debug(f" -----> {self.cache.path / self.path_within_cache}")
				self.download_to(path=self.cache.path / self.path_within_cache)
				
				# check again
				if expected_filepath.exists():
					self._filepath = expected_filepath
				else:
					raise NotImplementedError()
					
			self._filepath = expected_filepath

		return self._filepath
	
	@property
	def file_extension(self):
		'''
		Return the file extension, if there is one.
		'''
		return os.splitext(self.filename)[1]
	
	@property
	def is_in_cache(self) -> bool:
		'''
		Check if the resource is available locally, useful if one does not want to download it automatically.
		'''
		# If the file is found, sets self._filepath if not already set.
		return (self.cache.path / self.path_within_cache / self.filename).exists()
	
	def download_to(self, path:Union[pathlib.Path,str]=None):
		'''
		Download the resource to the specified directory. It will be decompressed if it's compressed from the source.
		
		:param path: the path to download the file to; does not include the filename
		'''
		logger.debug(f"path = {path}")
		if path is None:
			path = self.cache.path / self.path_within_cache
		elif isinstance(path, str):
			path = pathlib.Path(path)
		
		if self.is_in_cache:
			return
			
		if path.exists() == False:
			path.mkdir(parents=True)
			
		url = self.url
		ext = os.path.splitext(url)[1].lower() # file extension
		
		if ext in COMPRESSED_FILE_EXTENSIONS:
			# File is compressed on remote server. Download and decompress.
			if ext in [".gz"]:
				self._download_gz_file(url=url, path=path)
			elif ext in [".bz2", "bzip2"]:
				self._download_bz2_file(url=url, path=path)
			elif ext in [".zip"]:
				self._download_zip_file(url=url, path=path)
		
		else:
			# File is not compressed on the remote server.
			# Rather than read the whole thing into memory,
			# stream the data straight to a file on disk (making sure there are no errors).
			response = requests.get(url, stream=True)
			try:
				# raise "requests.HTTPError" exception if 400 <= status_code <= 600
				response.raise_for_status()
			except requests.HTTPError:
				if response.status_code == 404:
					logger.debug(f"404 File not found (url='{url}')")
		
			try:
				# Ref: https://2.python-requests.org//en/latest/user/quickstart/#raw-response-content
				with open(self.cache.path / self.cache_path / self.filename, mode='wb') as f:
					for chunk in response.iter_content(chunk_size=io.DEFAULT_BUFFER_SIZE):
						# chunk_size in bytes
						f.write(chunk)
			except requests.HTTPError as e:
				# .. todo:: handle different errors appropriately
				# - URL not found
				# - network error
				# - etc.
				raise NotImplementedError()
		
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
		
		ext = os.path.splitext(self.url)[1]
		fname = filename[:-len(ext)]
		logger.debug(f"fname={fname}")
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
				
		ext = os.path.splitext(self.url)[1]
		fname = filename[:-len(ext)]
		logger.debug(f"fname={fname}")
		path_to_write = path / self.filename # the SciID will have the uncompressed filename
		logger.debug(f"About to write file to: {path_to_write}")
		
		# note: zip files can contain multiple files
		# todo(?) support extracting metadata for multiple files in a zip archive
		ZipFile.extract(member=ZipFile(file=io.BytesIO(data)), path=path)
