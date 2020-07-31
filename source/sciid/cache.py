
import os
import pathlib
from typing import Union

class SciIDCache:
	'''
	A class that manages the data files retrieved by SciIDs; useful for repeated script runs.
	
	:param path: the SciID cache directory; defaults to `$HOME/.sciid_cache`
	'''
	
	_default_instance = None
	
	def __init__(self, path:Union[str,pathlib.Path]=pathlib.Path.home()/".sciid_cache"):
		#self.sciid_cache_path = None
		
		if isinstance(path, os.PathLike):
			pass
		elif isinstance(path, str):
			path = pathlib.Path(path)
		else:
			raise Exception(f"'path' must either be a str or os.PathLike object; was given '{type(path)}'.")

		self.path = path # creates directory if it doesn't exist

	@classmethod
	def default_cache(cls):
		'''
		A default cache manager that is preconfigured with default values designed to be used out of the box (batteries included).
		
		The default cache is located at `$HOME/.sciid_cache`, but can be changed by the user.
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
	
	