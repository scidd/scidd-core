
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

class SciDDCacheManagerBase(abc.ABC):

	@property
	@abc.abstractmethod
	def path(self) -> pathlib.Path:
		'''
		Return the top level path to the cache.
		'''
		pass

	# @path.setter
	# @abc.abstractmethod
	# def path(self, new_value):
	# 	pass

	@property
	@abc.abstractmethod
	def pathWithinCache(self, sci_dd) -> os.PathLike:
		'''
		Returns the path within the cache where the resource (file) would be found. Does not include the filename.
		'''
		pass

	def __repr__(self):
		return "<{0}.{1} object at {2} path='{3}'>".format(self.__class__.__module__, self.__class__.__name__, hex(id(self)), self.path)

	@abc.abstractproperty
	def localAPICache(self):
		'''
		A local database that caches API responses.
		'''
		pass

	@staticmethod
	def conforms_to_interface(instance):
		'''
		A utility method for other classes to check if they are compliant with this class' interface.

		It's recommended that this be called in the ``__init__`` method of any class that is acting as a SciDD cache manager.
		'''
		# check required properties
		for prop in ['path', 'localAPICache']:
			if not hasattr(instance, prop):
				raise TypeError(f"This class is a virtual subclass of scidd.SciDDCacheManagerBase; it must implement the property '{prop}'.")

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
		#self.scidd_cache_path = None

		if isinstance(path, os.PathLike):
			pass
		elif isinstance(path, str):
			path = pathlib.Path(path)
		else:
			raise Exception(f"'path' must either be a str or os.PathLike object; was given '{type(path)}'.")

		self._cache_path = path # creates directory if it doesn't exist


	@classmethod
	def default_cache(cls):
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
		return self._cache_path

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

		self._cache_path = new_path

	@property
	def localAPICache(self):
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

		# raise Exception()
		# if self._cache_path is None:
		# 	# remove prefix and leading "/"
		# 	self._cache_path = self.path.parent
		# 	logger.debug(f" cache_path = {self._cache_path} / {self.path}")
		# 	return self._cache_path

class LocalAPICache:
	'''
	This class manages a local database that caches requests/responses to the API to improve performance on repeated script runs.

	This class should be considered a private implementation detail and is not intended to be interacted with
	outside of this package.

	:param path: path where the database will be written to or found
	:param name: name of the cache file, defaults to ``_SciDD_API_Cache.sqlite``
	'''

	_default_instance = None

	def __init__(self, path:os.PathLike=pathlib.Path(".scidd_cache"), name:str="_SciDD_API_Cache.sqlite"):
		#if path is None:
		#	raise ValueError("The local API cache must have the 'path' parameter set.")
		self._path = path	# path to database
		self.name = name	# database filename
		self._db = None

		if not os.path.exists(self.path):
			os.makedirs(self.path)

	@property
	def path(self) -> os.pathLike:
		'''
		The full path where the cache database can be found (not including the filename).
		'''
		return self._path

	@path.setter
	def path(self, new_value:os.PathLike):
		'''
		The full path where the cache database can be found. The directory must exist before setting this value.

		Note that the path should be set before any access to the cache is made!
		'''
		if self._db is None:
			raise ValueError(f"The path cannot be changed after the first connection to the database is made.")
		if not new_value.exists():
			raise ValueError(f"The path to place the cache database must previously exist; '{new_value}' coud not be found.")
		if not os.access(new_value, os.W_OK | os.X_OK):
			raise ValueError(f"The cache path provided is not writable: '{new_value}'")
		self._path = new_value

	@classmethod
	def defaultCache(cls):
		'''
		A local API cache that is preconfigured with default values designed to be used out of the box (batteries included).

		By default a shared instance of :class:`SciDDCacheManager` is returned.
		The default cache is located at ``$HOME/.scidd_cache``, but can be changed by the user.
		There is only one instance of the default cache manager at any time, but it can be modified.
		'''
		if cls._default_instance is None:
			cls._default_instance = cls(path=SciDDCacheManager.default_cache().path) # use defaults
		return cls._default_instance

	@property
	def db_conn(self) -> sqlite3.Connection:
		'''
		An open connection to the SQLite database.
		'''
		if self._db is None:
			self._initial_database_connection() # defines self._db
		return self._db

	def _initial_database_connection(self):
		'''
		Make the initial connection to the database.
		'''
		db_filepath = self.path / self.name
		is_new_database = not db_filepath.exists()

		#print(db_filepath)
		if self.path.is_symlink(): # or os.path.islink(fp)
			#print("is symlink")
			if not os.path.exists(os.readlink(self.path)):
				# broken link
				raise Exception(f"The path where the SciDD cache is expected ('{self.path}') is symlink pointing to a target that is no longer there. " +
			                    "Either remove the symlink or fix the destination.")

		try:
			self._db = sqlite3.connect(db_filepath)
		except sqlite3.OperationalError as e:
			if is_new_database:
				raise Exception(f"Unable to create database at specified path ('{db_filepath}').")
			else:
				raise Exception(f"Found file at path '{path / self.name}', but am unable to open as an SQLite database.")

		self._configure_db_connection(self.db_conn)

		if is_new_database:
			self._init_sqlite_db()

	def __del__(self):
		''' Destructor method - close database connection when object is no longer needed. '''
		# if we had an open SQLite connection, close it
		if self._db:
			self._db.close()

	def _configure_db_connection(self, dbconn):
		'''
		Configure connection-level settings on the SQLite database.
		'''
		# set database-specific settings
		#dbconn.isolation_level = None    # autocommit mode; transactions can be explicitly created with BEGIN/COMMIT statements
		dbconn.row_factory = sqlite3.Row # return dictionaries instead of tuples from SELECT statements

	def _init_sqlite_db(self):
		'''
		Initialize a new index database, e.g. create schema, initialize metadata.
		'''
		with contextlib.closing(self.db_conn.cursor()) as cursor:

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

	def __getitem__(self, key):
		'''
		The cache is made to look like a key/value store.
		'''
		# this demonstrates a simple implementation: https://stackoverflow.com/a/47240886/2712652
		value = self.db_conn.execute("SELECT json_response FROM cache WHERE query=?", (key,)).fetchone()
		if value is None:
			raise KeyError(key)
		return value[0]

	def __setitem__(self, key, value):
		'''
		The cache is made to look like a key/value store.
		'''
		with contextlib.closing(self.db_conn.cursor()) as cursor:
			cursor.execute("REPLACE INTO cache (query, json_response) VALUES (?,?);", (key, value))
			self.db_conn.commit()

