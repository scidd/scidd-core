
from __future__ import annotations # remove in Python 4.0
# Needed for forward references, see:
# https://stackoverflow.com/a/33533514/2712652

import io
import os
import sys
import bz2
import pdb
import gzip
import time
import shutil
import urllib
import pathlib
from typing import Union
from zipfile import ZipFile
from abc import ABC, abstractproperty, abstractmethod

import astropy
import requests

import scidd
from . import exc
from .cache import SciDDCacheManager, SciDDCacheManagerBase
from .resolver import Resolver
from .logger import scidd_logger as logger

# list of file extensions that we treat as compressed files
COMPRESSED_DOT_FILE_EXTENSIONS = [".gz", ".bz2", ".zip"]

def set_file_time_to_last_modified(filepath, response):
	'''
	If the 'Last-Modified' header is found in the response, update the downloaded file's timestamp to that date.
	'''
	try:
		srvLastModified = time.mktime(time.strptime(response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S GMT"))
		os.utime(filepath, (srvLastModified, srvLastModified))
	except KeyError:
		# "Last-Modified" header not present
		pass


class SciDD(): #, metaclass=SciDDMetaclass):
	'''
	This class is wrapper around SciDD identifiers.

	:param sci_dd: the SciDD identifier
	'''
	def __init__(self, sci_dd:str=None, resolver=None):
		if sci_dd is None:
			raise ValueError("An identifier must be provided.")
		if isinstance(sci_dd, dict):
			raise ValueError("The 'sci_dd' value should be a string, not a dictionary. Maybe you forgot to extract the value from an API result?")
		self._scidd = sci_dd # string representation of the identifier
		self.resolver = resolver
		self._url = None # a place to cache a URL once the record has been resolved

		# note: only minimal validation is being performed
		if self.isValid() is False:
			raise ValueError(f"The provided identifier was not validated as a valid SciDD ('sci_dd').")

		# set the resolver
		# if resolver is None:
		# 	raise exc.ValidResolverNotFound("A valid resolver for this SciDD was not specified or else a default resolver not provided.")

	def __new__(cls, sci_dd:str=None, resolver=None):
		'''
		SciDD is a factory class; if the prefix is identified as having a subclass dedicated to it, that subclass is instantiated.
		'''
		# Useful ref: https://stackoverflow.com/a/5953974/2712652
		if type(cls) == type(SciDD):
			if str(sci_dd).startswith("scidd:/astro"):
				from scidd.astro import SciDDAstro, SciDDAstroFile
				if "/file/" in str(sci_dd):
					return SciDDAstroFile.__new__(SciDDAstroFile, sci_dd=sci_dd, resolver=resolver)
				else:
					return SciDDAstro.__new__(SciDDAstro, sci_dd=sci_dd, resolver=resolver)
			# if sci_dd.startswith("scidd:/astro/data/"):
			# 	return super().__new__(scidd.astro.SciDDAstroData)
			# elif sci_dd.startswith("scidd:/astro/file/"):
			# 	return super().__new__(scidd.astro.SciDDAstroFile)
		return super().__new__(cls)

	def __str__(self):
		# this is useful so one can use str(s), and "s" can be either a string or SciDD object.
		return self._scidd

	def __repr__(self):
		return f"<scidd.astro.{self.__class__.__name__} object at {hex(id(self))} '{self._scidd}'>"

	@property
	def scidd(self) -> str:
		''' Returns a string representation of the identifier. '''
		return self._scidd

	@scidd.setter
	def scidd(self, new_id):
		if not isinstance(new_id, str):
			raise ValueError("The 'scidd' property must be a string.")
		self._scidd = new_id

	def isValid(self) -> bool:
		'''
		Performs (very) basic validation of the syntax of the identifier

		This method performs minimal validation; subclasses are expected to
		perform more rigorous but not necessarily exhaustive checks.

		:returns: ``True`` if this generally looks like an identifier, ``False`` if not
		'''
		# sometimes it might be beneficial for overriding classes to call super, other times it's inefficient and redundant.
		return self.scidd.startswith("scidd:/")

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
				raise exc.NoResolverAssignedException("Attempting to resolve a SciDD without having first set a resolver object.")

			self._url = self.resolver.urlForSciDD(self)

		return self._url

	@url.setter
	def url(self, new_value):
		self._url = new_value

	@property
	def path(self) -> str:
		'''
		Returns the SciDD as a string without the scheme prefix (i.e. the ``scidd:`` prefix is removed).
		'''
		return str(self).replace('scidd:', '')

	@property
	def fragment(self) -> str:
		'''
		The fragment part of the SciDD; this component of the string identifies data within the resource.
		'''
		if "#" in self._scidd:
			return self._scidd.split("#")[1]
		else:
			return None

	@fragment.setter
	def fragment(self, new_fragment):
		'''
		Add the provided string as a fragment to this SciDD.
		'''
		if "#" in self._scidd:
			# already has a fragment
			self._scidd = self._scidd.sciDDWithoutFragment()
		self._scidd = "#".join(self._scidd, new_fragment)

	def sciDDWithoutFragment(self) -> SciDD:
		'''
		Returns a new SciDD object that is stripped of the fragment (if there is one).
		'''
		return SciDD(str(self).split("#")[0])

	@property
	def metadata(self) -> dict:
		'''
		Returns metadata of this file as a dictionary. [Format to be determined.]
		'''
		raise NotImplementedError()

	@classmethod
	def fromFilename(cls, filename:str, domain:str, allow_multiple_results=False) -> SciDD:
		'''
		A factory method that attempts to return a SciDD identifier from a filename alone; depends on domain-specific resolvers.

		:param filename: the filename to create a SciDD identifier from
		:param domain: the top level domain of the resource, e.g. ``astro``: todo: create a .scidd.conf file with a default domain setting
		:param allow_multiple_results: when True will raise an exception the filename is not unique; if False will always return an array of matching SciDDs.
		'''
		if filename is None or len(filename) == 0:
			raise ValueError("A filename must be provided.")
		if domain == "astro":
			from scidd.astro import SciDDAstroFile
			#return SciDDAstroFile.__new__(SciDDAstro, sci_dd=sci_dd, resolver=resolver)
			# .. todo: check here if the path looks like a file in the first place
			return SciDDAstroFile.fromFilename(filename=filename, allow_multiple_results=allow_multiple_results)
		else:
			raise NotImplementedError(f"The top level domain '{domain}' is not currently implemented (the only domain currently implemented is 'astro'.")

class SciDDFileResource:
	'''
	This class represents a :class:`SciDD` identifier that specifically points to and helps manage a file resource.

	It provides additional properties, methods, and utility that is useful for working with files.
	'''

	# Class variables
	# ---------------
	# Use this cache manager for all new SciDDs (that point to files, of course).
	# Note that this is a class variable! Changing it will not change any
	# previously set cache manager on existing SciDDFileResource objects.
	_default_cache_manager = SciDDCacheManager.defaultCache()

	def __init__(self):
		self._filepath = None # store local location
		self._filename = None # cache the filename derived from the identifier
		self.read_only_caches = list() # list of SciDDCacheManager objects that point to read-only caches

		# .. todo:: this doesn't seem to be used anywhere.
		#self._filename_unique_identifier = None # a string used to disambiguate files with the same name in the same dataset release

		if __class__._default_cache_manager is None:
			self.cache = SciDDCacheManager.defaultCache()
		else:
			self.cache = __class__._default_cache_manager

		# information retrieved from the Trillian API, used to test successful download of file, todo: can also use hash but will be slower
		self._uncompressed_file_size = None

		# Caches
		# A SciDD is an "abstract" representation of the data. A file (in this case) can be located
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
	# 	for ext in COMPRESSED_DOT_FILE_EXTENSIONS:
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

		    scidd:/astro/data/2mass/allsky/hi0550232.fits;uniqueid=20000116.n.55?a=b

		The optional ``;uniqueid=20000116.n.55`` fragment is not part of the filename and is delineated by the ``;`` character.
		The optional query component ``a=b`` is delineated by the first ``?``.
		Removing both and returning the final path component yields the filename.
		'''
		if self._filename is None:
			path = self.path # remove scheme
			path = path.split(";")[0] # remove scheme-specific segment
			self._filename = os.path.basename(path)
		return self._filename

	@filename.setter
	def filename(self, new_filename:str):
		'''
		Note! Setting the ``filename`` property is considered an internal method and should *not* be used.
		'''
		# This is here so that when the filename property is set, "self._filepath" is returned to None to recalculate.
		self._filename = new_filename
		self._filepath = None

	@property
	def filepath(self) -> pathlib.Path:
		'''
		Return local file path for resource, including the filename; download if needed.

		Note: Using autocomplete in an interactive environment (e.g. Jupyter notebook, iPython)
		on a SciDD object will cause the associated file to be downloaded if it's not found on disk.
		'''
		if self._filepath is None:
			# already in cache?
			expected_filepath = self.cache.path / self.pathWithinCache() / self.filename
			if expected_filepath.exists():
				self._filepath = expected_filepath
				#logger.debug(f'Found in cache: "{expected_filepath}"')
				return self._filepath
			# File was not found. If a compressed version exists, use that.
			# If not, download the file.
			#
			for ext in COMPRESSED_DOT_FILE_EXTENSIONS:
				path = expected_filepath.parent / f"{expected_filepath.name}{ext}"
				logger.debug(f"checking: {path}")
				if path.exists():
					self._filepath = path
					return self._filepath

			# Not found; download the file.
			#logger.debug(f" -----> {self.cache.path / self.pathWithinCache}")
			expected_filepath = self.downloadTo(path=expected_filepath.parent) #self.cache.path / self.pathWithinCache)

			# double check
			if expected_filepath.exists():
				self._filepath = expected_filepath
			else:
				raise NotImplementedError(f"Expected to find file at '{expected_filepath}, but not found ({self.filename=}).'")

		return self._filepath

	@property
	def fileExtension(self) -> str:
		'''
		Return the file extension, if there is one.
		'''
		return os.splitext(self.filename)[1]

	def pathWithinCache(self, cache:SciDDCacheManagerBase=None) -> pathlib.Path:
		'''
		Returns the path where this resource should be placed/found for the given cache manager.

		A SciDD is an "abstract" representation of the data. A file (in this case) can be located
		in multiple caches managed by the same program. The dictionary below stores the path
		location within each cache it encounters (i.e. relative to the top level of the cache).

		Usually the default cache manager is the right choice and the parameter can be omitted.

		:param cache: an object that implements the ``scidd.core.SciDDCacheManagerBase`` protocol
		'''
		if cache is None:
			cache = self.cache
		try:
			return self._path_within_cache[cache]
		except KeyError:
			path = cache.pathWithinCache(sci_dd=self)
			self._path_within_cache[cache] = path
			assert not str(path).startswith("/"), "This causes problems when joining paths."
			return path

	def isInCache(self) -> bool:
		'''
		Check if the resource is available locally, useful if one does not want to download it automatically.

		This method will look for zero-length files (e.g. if there was a previous error or code interrupted).
		In this case, the file will be deleted and ``False`` will be returned.
		'''
		# If the file is found, sets self._filepath if not already set.
		full_path = self.cache.path / self.pathWithinCache() / self.filename
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

		# In principle, this method should be the "choke point" of downloading data,
		# i.e. no downloads should occur outside of this method.

		logger.debug(f"downloading '{self.url}' to: '{path}'")
		#raise Exception("break here to catch when files are being downloaded")

		if path is None:
			path = self.cache.path / self.pathWithinCache()
		elif isinstance(path, str):
			path = pathlib.Path(path)

		if self.isInCache(): # checks for zero length file; if found, deletes and returns False
			return self.filepath

		if os.path.lexists(path):
			# 'lexists' returns True for broken symbolic links;
			# useful to avoid attempting to create a directory on top of a broken link (which will crash)

			# is this a broken link?
			if path.exists() is False:
				raise Exception(f"Tried to set up a cache directory but found what appears to be a broken symbolic link: '{path}'")
		else:
			path.mkdir(parents=True)

		url = self.url
		ext = os.path.splitext(url)[1].lower() # file extension

		target_file_is_compressed = ext in COMPRESSED_DOT_FILE_EXTENSIONS

		if target_file_is_compressed and self.cache.decompressDownloads:
			self._filepath = self._download_compressed_file(url=url, ext=ext, path=path) # <- decompresses file
			self._filename = p.name
			return self.filepath

		#status = None
		# File is not compressed on the remote server.
		# Rather than read the whole thing into memory,
		# stream the data straight to a file on disk (making sure there are no errors).
		try:
			response = requests.get(url, stream=True) # make connection to remote server
			destination_file = self.cache.path / self.pathWithinCache() / os.path.basename(url) #self.filename
			logger.debug(f"A {destination_file=}")
		except requests.exceptions.ConnectionError as err:
			if "HTTPSConnectionPool" in str(err):
				if "Max retries exceeded with url" in str(err):
					raise exc.InternetConnectionError(f"Could not connect to the host '{urllib.parse.urlparse(self.url).hostname}'; exceeded the maximum number of attempts. Are you connected to the internet or could the host be blocked for some reason?")
				else:
					raise NotImplementedError("Handle errors here!")
			else:
				raise NotImplementedError("Handle errors here!")

		# check status to remote connection (file found? not found?)
		try:
			response.raise_for_status() # request "requests.HTTPError" exception if 400 <= status_code <= 600
		except requests.HTTPError:
			if response.status_code == 404:
				logger.debug(f"404 File not found (url='{url}')")

				# File was not found. Try again with common file compression suffixes?
				file_found = False
				for ext in COMPRESSED_DOT_FILE_EXTENSIONS:
					# where are you mr file?
					if requests.head(url+ext).status_code == 200: # found file
						url = url + ext
						file_found = True

						logger.warning(f"The Trillian API expected a file to be located at '{url[0:-len(ext)]}'; found instead at '{url}'.")
						if self.cache.decompressDownloads:
							self._filepath = self._download_compressed_file(url=url, ext=ext, path=path)
							self._filename = p.name
							return self.filepath
						else:
							response = requests.get(url, stream=True)
							self.filename = os.path.basename(url) # update filename to have the compressed extension
							destination_file = self.cache.path / self.pathWithinCache() / self._filename
							logger.debug(f"{destination_file=}")
							logger.debug(f"{url=}")
							# download below
						break

				if file_found is False:
					logger.warning(f"No file was found as expected at '{url}' or with any known compression extension.")
					raise exc.FileResourceCouldNotBeFound(f"No file found where the Trillian API service expected to be found (even after looking for compressed versions of the file ('{url}').")
			else:
				raise NotImplementedError(f"Encountered status {response.status_code} in file download request, but not handled.")

		# file found, download
		try:
			# Ref: https://2.python-requests.org//en/latest/user/quickstart/#raw-response-content
			#destination_file = self.cache.path / self.pathWithinCache() / self.filename
			# stream data straight to disk instead of loading whole file into RAM
			with open(destination_file, mode='wb') as f:
				for chunk in response.iter_content(chunk_size=io.DEFAULT_BUFFER_SIZE):
					# chunk_size in bytes
					f.write(chunk)

			# set file time to that on server
			set_file_time_to_last_modified(destination_file, response)
			return destination_file

		except requests.HTTPError as e:
			# .. todo:: handle different errors appropriately
			# - URL not found
			# - network error
			# - etc.
			raise NotImplementedError()

	def _download_compressed_file(self, url:str, ext:str, path:os.pathLike) -> os.pathLike:
		'''
		Download the provided file that's compressed on the remote server and decompress the returned file.

		This is an internal implementation detail that should not be called outside of this class and is subject to change or removal.

		:param url: the full URL to the file to be downloaded
		:param ext: the file's extension, including the leading fullstop, e.g. `.gz`
		:param path: the local filesystem path to down the file into
		:returns: path (including filename) the file was downloaded to
		'''
		# File is compressed on remote server. Download and decompress.
		if ext in [".gz"]:
			return self._download_gz_file(url=url, path=path)
		elif ext in [".bz2", ".bzip2"]:
			return self._download_bz2_file(url=url, path=path)
		elif ext in [".zip"]:
			return self._download_zip_file(url=url, path=path)
		else:
			raise NotImplementedError(f"Files compressed with the extension '{ext}' are not yet supported.")

	def _download_gz_file(self, url:str, path:pathlib.Path):
		'''
		Private method that downloads a URL that points to a gzip compressed file. Resulting file is decompressed.

		:param url: the URL to download as a string
		:param path: the local location where to download the file to
		:returns: path (including filename) the file was downloaded to
		'''
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
		path_to_write = path / self.filename # the SciDD will have the uncompressed filename
		logger.debug(f"About to write file to: {path} / {self.filename}")

		with open(path_to_write, 'wb') as f:
			shutil.copyfileobj(io.BytesIO(gzip.decompress(response.content)), f)

		# set file time to that on server
		set_file_time_to_last_modified(path_to_write, response)

		return path_to_write

	def _download_bz2_file(self, url:str, path:pathlib.Path):
		'''
		Private method that downloads a URL that points to a bz2 compressed file. Resulting file is decompressed.

		:param url: the URL to download as a string
		:param path: the local location where to download the file to
		:returns: path (including filename) the file was downloaded to
		'''
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
		path_to_write = path / self.filename # the SciDD will have the uncompressed filename
		logger.debug(f"About to write file to: {path_to_write}")

		with open(path_to_write, 'wb') as f:
			shutil.copyfileobj(io.BytesIO(bz2.decompress(response.content)), f)

		set_file_time_to_last_modified(path_to_write, response)

		return path_to_write

	def _download_zip_file(self, url:str, path:pathlib.Path) -> os.pathLike:
		'''
		Private method that downloads a URL that points to a zip compressed file. Resulting file is decompressed.

		:param url: the URL to download as a string
		:param path: the local location where to download the file to
		:returns: path (including filename) the file was downloaded to
		'''
		response = requests.get(url=url)
		try:
			response.raise_for_status()
		except requests.HTTPError:
			if response.status_code == 404:
				raise NotImplementedError() # handle error

		#ext = os.path.splitext(self.url)[1]
		#fname = filename[:-len(ext)]
		#logger.debug(f"fname={fname}")
		path_to_write = path / self.filename # the SciDD will have the uncompressed filename
		logger.debug(f"About to write file to: {path_to_write}")

		# note: zip files can contain multiple files
		# todo(?) support extracting metadata for multiple files in a zip archive
		ZipFile.extract(member=ZipFile(file=io.BytesIO(data)), path=path)

		set_file_time_to_last_modified(path_to_write, response)

		return path_to_write
