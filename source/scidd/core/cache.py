
from __future__ import annotations # remove in Python 3.10
# Needed for forward references, see:
# https://stackoverflow.com/a/33533514/2712652

import os
import re
import abc
import pdb
import scidd
import pathlib
import sqlite3
import contextlib
from typing import Union

from .logger import scidd_logger as logger

class SciDDCacheManagerBase(metaclass=abc.ABCMeta):

	@property
	@abc.abstractmethod
	def path(self) -> pathlib.Path:
		'''
		Return the top level path to the cache.
		'''
		pass

	@abc.abstractmethod
	def pathWithinCache(self, sci_dd) -> os.PathLike:
		'''
		Returns the path within the cache where the resource (file) would be found. Does not include the filename.
		'''
		pass

	def __repr__(self):
		return "<{0}.{1} object at {2} path='{3}'>".format(self.__class__.__module__, self.__class__.__name__, hex(id(self)), self.path)

	@property
	def decompressDownloads(self) -> bool:
		'''
		If ``True``, downloaded data that is found compressed (e.g. .gz, .zip) will be decompressed into the cache. Default is ``False``.
		'''
		if not hasattr(self, '_decompressDownloads'):
			self._decompressDownloads = False
		return self._decompressDownloads

	@decompressDownloads.setter
	def decompressDownloads(self, new_value:bool):
		if not hasattr(self, '_decompressDownloads'):
			self._decompressDownloads = False
		try:
			self._decompressDownloads = bool(new_value)
		except ValueError:
			raise ValueError(f"The 'decompressDownloads' property requires a Boolean value.")

	@abc.abstractproperty
	def localAPICache(self) -> SciDDCacheManagerBase:
		'''
		A local database that caches API responses.
		'''
		pass

	@staticmethod
	def conformsToInterface(instance) -> bool:
		'''
		A utility method for other classes to check if they are compliant with this class' interface.

		It's recommended that this be called in the ``__init__`` method of any class that is acting as a SciDD cache manager.
		'''
		# check required properties
		for prop in ['path', 'localAPICache']:
			hasattr(instance, prop) # Oddly, returns 'False' the first time, 'True' the second (if available).
			if not hasattr(instance, prop):
				raise TypeError(f"The class '{instance.__class__}' is a virtual subclass of scidd.SciDDCacheManagerBase; it must implement the property '{prop}'.")

		# check callable methods
		if not callable(instance.pathWithinCache):
			raise TypeError(f"This class is a virtual subclass of scidd.SciDDCacheManagerBase; it must implement the method 'pathWithinCache'.")

class SciDDCacheManager(SciDDCacheManagerBase):
	'''
	A class that manages the data files retrieved by SciDDs; useful for repeated script runs.

	:param path: the SciDD cache directory; defaults to ``$HOME/.scidd_cache``.
	'''

	_default_instance = None

	def __init__(self, path:Union[str,pathlib.Path]=pathlib.Path(f"{pathlib.Path.home()}") / ".scidd_cache"):
		super().__init__()

		if isinstance(path, os.PathLike):
			pass
		elif isinstance(path, str):
			path = pathlib.Path(path)
		else:
			raise Exception(f"'path' must either be a str or os.PathLike object; was given '{type(path)}'.")

		self._cache_parent_directory = path # creates directory if it doesn't exist

	@classmethod
	def defaultCache(cls):
		'''
		A cache manager that is preconfigured with default values designed to be used out of the box (batteries included).

		The default cache is located at ``$HOME/.scidd_cache``, but can be changed by the user.
		There is only one instance of the default cache manager at any time, but it can be modified.
		'''
		if cls._default_instance is None:
			cls._default_instance = cls() # use defaults
		return cls._default_instance

	@property
	def path(self) -> pathlib.Path:
		'''
		The directory used to download files to.
		'''
		return self._cache_parent_directory

	@path.setter
	def path(self, new_path:Union[str,pathlib.Path]=None):
		'''
		Set the top level cache to the provided directory.

		:param new_path: the path to set for the cache
		'''
		if new_path is None:
			raise ValueError("The cache path cannot be set to 'None'.")
		elif isinstance(new_path, str):
			new_path = pathlib.Path(new_path)

		if new_path.exists() is False:
			try:
				new_path.mkdir(exist_ok=True)
			except PermissionError as e:
				raise PermissionError(f"You do not have permission to write to the provided cache path ('{new_path}'). Error: {e}")

		# is the directory actually a directory and writable?
		if os.path.isdir(new_path) == False:
			raise Exception(f"The provided cache directory value ('{new_path}') is not a directory.")
		elif os.access(new_path, mode=os.W_OK) == False:
			raise Exception(f"The provided cache directory ({new_path}) is not writable (check permissions?).")

		self._cache_parent_directory = new_path

	@property
	def localAPICache(self) -> LocalAPICache:
		'''
		A local database that caches API responses.
		'''
		if not hasattr(self, '_localAPICache'):
			self._localAPICache = LocalAPICache.defaultCache()
			self._localAPICache.path = self.path
			#self._localAPICache.parentCache = self
		return self._localAPICache

	def pathWithinCache(self, sci_dd:SciDDFileResource) -> os.PathLike:
		'''
		The directory path within the top level SciDD cache where the file would be written when downloaded.

		This can be domain-specific, e.g. a collection that has millions of files might be better served
		with a custom scheme. It's recommended to subclass this class for such files.
		'''
		# remove prefix and leading "/"

		try:
			return sci_dd._path_within_cache[self]
		except KeyError:
			p = str(pathlib.Path(sci_dd.path).parent).lstrip("/")
			assert not p.startswith("/"), "This causes problems!"

			# remove the "/file/" component; it's redundant
			match = re.search("^([^/]+)/file/(.+)", p)
			if match:
				p = f"{match.group(1)}/{match.group(2)}"
			sci_dd._path_within_cache[self] = p
			#logger.debug(f" path_within_cache = '{p}'")
			return p

class LocalAPICache:
	'''
	This class manages a local database that caches requests/responses to the API to improve performance on repeated script runs.

	The cache is thread-safe and multiprocessing safe.

	This class should be considered a private implementation detail and is not intended to be interacted with
	outside of this package.

	:param path: path where the database will be written to or found
	:param name: name of the cache file, defaults to ``_SciDD_API_Cache.sqlite``
	'''

	_default_instance = None

	def __init__(self, path:os.PathLike=pathlib.Path.home()/".scidd_cache", name:str="_SciDD_API_Cache.sqlite"):

		self._dbFilepath = path / name # the full path + filename for the cache

		# create database path if needed
		if not path.exists():
			try:
				os.makedirs(path)
			except FileExistsError as e:
				logger.debug(f"Path '{path}' appears not to exist, but 'os.makedirs(path)' is raising FileExistsError: {e}")
			except OSError as e:
				raise OSError(f"Unable to create specified path '{path}'; error: {e} ")

		if path.is_symlink(): # or os.path.islink(fp)
			if not os.path.exists(os.readlink(path)):
				# broken link
				raise Exception(f"The path where the SciDD cache is expected ('{path}') is symlink pointing to a target that is no longer there. " +
			                    "Either remove the symlink or fix the destination.")

		self._initialize_database()

	@property
	def dbFilepath(self) -> os.PathLike:
		'''
		Returns the path of the SQLite database cache.
		'''
		# The main purpose of this method is to check that the database exists and
		# create it if it doesn't or was deleted during the run of a program.

		if self._dbFilepath.exists():
			if self._dbFilepath.stat().st_size == 0: # size in bytes
				self._dbFilepath.unlink()
				self._initialize_database()
		else:
			self._initialize_database()

		return self._dbFilepath

	@property
	def path(self) -> pathlib.Path:
		'''
 		The full path where the cache database can be found (not including the filename).
		'''
		return self.dbFilepath.parent

	@classmethod
	def defaultCache(cls) -> LocalAPICache:
		'''
		A local API cache that is preconfigured with default values designed to be used out of the box (batteries included).

		By default a shared instance of :class:`SciDDCacheManager` is returned.
		The default cache is located at ``$HOME/.scidd_cache``, but can be changed by the user.
		There is only one instance of the default cache manager at any time, but it can be modified.
		'''
		if cls._default_instance is None:
			cls._default_instance = cls(path=SciDDCacheManager.defaultCache().path) # use defaults
		return cls._default_instance

	# @property
	# def db_conn(self) -> sqlite3.Connection:
	# 	'''
	# 	An open connection to the SQLite database.
	# 	'''
	# 	if self._db is None:
	# 		self._initial_database_connection() # defines self._db
	# 	return self._db

	def _initialize_database(self):
		'''
		Make the initial connection to the database, creating file/schema as needed.
		'''
		#db_filepath = self.path / self.name
		is_new_database = not self._dbFilepath.exists() # not db_filepath.exists()

		#with contextlib.closing(sqlite3.connect(self.dbFilepath, timeout=20)) as connection:
		#	with contextlib.closing(connection()) cursor as cursor):

		try:
			connection = sqlite3.connect(self._dbFilepath, timeout=20)
		except sqlite3.OperationalError as e:
			if is_new_database:
				raise Exception(f"Unable to create database at specified path ('{db_filepath}').")
			else:
				raise Exception(f"Found file at path '{path / self.name}', but am unable to open as an SQLite database.")

		with contextlib.closing(connection):
			# configure connection-level settings on the SQLite database
			# ----------------------------------------------------------
			#connection.isolation_level = None    # autocommit mode; transactions can be explicitly created with BEGIN/COMMIT statements
			connection.row_factory = sqlite3.Row  # return dictionaries instead of tuples from SELECT statements

			#self._configure_db_connection(self.db_conn)

			if is_new_database:
				self._init_sqlite_db(connection)

	#def __del__(self):
	#	''' Destructor method - close database connection when object is no longer needed. '''
	#	# if we had an open SQLite connection, close it
	#	if self._db:
	#		self._db.close()

	#def _configure_db_connection(self, dbconn):
	#	'''
	#	Configure connection-level settings on the SQLite database.
	#	'''
	#	# set database-specific settings
	#	#dbconn.isolation_level = None    # autocommit mode; transactions can be explicitly created with BEGIN/COMMIT statements
	#	dbconn.row_factory = sqlite3.Row # return dictionaries instead of tuples from SELECT statements

	def _init_sqlite_db(self, connection:sqlite3.Connection):
		'''
		Initialize a new index database, e.g. create schema, initialize metadata.
		'''
		with contextlib.closing(connection.cursor()) as cursor:

			cursor.execute('''
				CREATE TABLE metadata (
					id INTEGER PRIMARY KEY,
					date_created DATE,
					database_version INTEGER
				);''')

			cursor.execute(''' INSERT INTO metadata (id, date_created, database_version) VALUES (1, CURRENT_TIMESTAMP, 1); ''')

			# may just change this to "key","value" if this doesn't grow beyond a simple ket/value store
			cursor.execute('''
				CREATE TABLE cache (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					query TEXT UNIQUE,
					json_response TEXT
				);''')

			cursor.execute('''CREATE UNIQUE INDEX query_idx ON cache(query)''');
			connection.commit()

	def __getitem__(self, key):
		'''
		The cache is made to look like a key/value store.
		'''

		if not self.dbFilepath.exists():
			logger.debug("no db file found")

		# use URI method to supply connection options (here, read-only)

		# this demonstrates a simple implementation: https://stackoverflow.com/a/47240886/2712652
		with contextlib.closing(sqlite3.connect(f"file:{self.dbFilepath}?mode=ro", uri=True, timeout=30)) as connection:
			with contextlib.closing(connection.cursor()) as cursor:
				value = cursor.execute("SELECT json_response FROM cache WHERE query=?", (key,)).fetchone()
				if value is None:
					raise KeyError(key)
				else:
					return value[0]

	def __setitem__(self, key, value):
		'''
		The cache is made to look like a key/value store.
		'''

		# isolation_level=None puts the connection in autocommit mode

		with contextlib.closing(sqlite3.connect(self.dbFilepath, isolation_level=None, timeout=30)) as connection:
			with contextlib.closing(connection.cursor()) as cursor:
				cursor.execute('pragma journal_mode=wal') # https://stackoverflow.com/questions/47250220/using-sqlite-with-wal
				cursor.execute("REPLACE INTO cache (query, json_response) VALUES (?,?);", (key, value))
				#connection.commit() # not needed when isolation_level=None
