import os
from .. import SciID
from . import SciIDResolverAstro

compression_extensions = [".zip", ".tgz", ".gz", "bz2"]

class SciIDAstro(SciID):
	'''
	This class is wrapper around SciID identifiers in the 'astro' namespace ("sciid:/astro").
	
	:param sciid: a SciID identifier or one assumed to have "sciid:/astro" prepended to it
	:param resolver: an object that can resolve the identifier to a URL; for most cases using the default resolver by passing 'None' is the right choice
	'''
	def __init__(self, id_:str=None, resolver=SciIDResolverAstro.default_resolver()):
		print("sciidastro __init__")
		if not id_.startswith("sciid:/astro/") and id_.startswith("/"):
			# allow abbreviated form
			id_ = "sciid:/astro" + id_
		super().__init__(id_=id_, resolver=resolver)
	
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
		return str(self.sciid).split("/")[1] # first string after "data/"
	
	# def __new__(cls, sciid:str=None, resolver=None):
	# 	'''
	# 	'''
	# 	if sciid.startswith("sciid:/astro/data/"):
	# 		return SciIDAstroData(sciid=sciid)
	# 	elif sciid.startswith("sciid:/astro/file/"):
	# 		return SciIDAstroFile(sciid=sciid)
	
class SciIDAstroData(SciIDAstro):
	'''
	An identifier pointing to data in the astronomy namespace ("sciid:/astro/data/").
	'''
	def __init__(self, id_:str=None, resolver=None):
		if id_.startswith("sciid:") and not id_.startswith("sciid:/astro/data/"):
			raise exc.SciIDClassMismatch(f"Attempting to create {self.__class__} object with a SciID that does not begin with 'sciid:/astro/data/'; try using the 'SciID(id_)' factory constructor instead.")
		super().__init__(id_=id_, resolver=resolver)
	
	def is_file(self) -> bool:
		''' Returns 'True' if this identifier points to a file. '''
		return False

	def is_valid_id(self) -> bool:
		'''
		Performs basic validation of the syntax of the identifier; a returned value of 'True' does not guarantee a resource will be found.
		'''
		return self.sciid.startswith("sciid:/astro/data/")
		
	
	
class SciIDAstroFile(SciIDAstro):
	'''
	An identifier pointing to a file in the astronomy namespace ("sciid:/astro/file/").
	'''
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
			
	
