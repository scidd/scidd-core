
from .. import SciIDAstro
from ... import exc
from ... import SciIDFileResource

class SciIDAstroFile(SciIDAstro, SciIDFileResource):
	
	@property
	def cache_path_unique_identifier(self) -> str:
		'''
		A unique identifier to include in a cache path to disambiguate files since 2MASS filenames are not unique within the data release.
		'''
		path = None
		match = re.search("^.+;([^?].+)", self.path)
		if match:
			# maybe move this logic to subclasses specific to the dataset
			for key, value in [pair.split("=") for pair in match.group(1).split("?")]:
				if key == "uniqueid":
					path = os.path.join(ipix_path_within_cache, key)
					break
			assert path is not None, f"Expected to find a unique identifier for a filename, but one was not found: {sci_id}".
		else:
			raise exc.UnexpectedSciIDFormatException("Format of 2MASS SciID not as expected.")
	
	def unique_identifier_for_filename(self) -> str:
		'''
		Returns a string that can be used as a unique identifier to disambiguate files within the dataset that have the same name.
		
		The default returns an empty string as it is assumed filenames within a dataset are unique;
		override this method to return an identifier when this is not the case.		
		'''
		match = re.search(";([^?].+)", self.path)
		if match:
		#	# use this if more terms are added to the ";..." segment
		#	for key, value in [pair.split("=") for pair in match.group(1).split("?")]:
		#		if key == "uniqueid":
		#			break
			_,identifier = match.group(1).split("=")
			return identifier
		else:
			raise exc.UnexpectedSciIDFormatException(f"Expected to find a unique identifier for a filename, but one was not found: '{sci_id}'.")

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
	
			records = sciid.API().get(path="/astro/data/filename-search", params=parameters)
	
			# Expect to get back all records that match this filename (there can be many).
			# Find the matching one.
			uniqueid = self.unique_identifier_for_filename
			for rec in records:
				sci_id = record["sciid"]
				if uniqueid in sci_id:
					logger.debug(record)
					pos = record["position"] # array or two points
					self._position = SkyCoord(ra=pos[0]*u.deg, dec=pos[1]*u.deg)
	
					# while we're here...
					if self._url is None:
						self._url = record["url"]
						self._uncompressed_file_size = record["file_size"]
					break
		
			logger.debug(f"Could not find a position for '{self}'!")
				
		return self.position
		