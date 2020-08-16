
import re
import json
from abc import ABC, abstractmethod, abstractproperty

from ... import exc
from ...logger import sciid_logger as logger

# class DatasetResolverBaseMeta(type):
# 	@staticmethod
# 	def resolve_filename(sci_id) -> str:
# 		return DatasetResolverBase.resolve_filename_from_release(sci_id=sci_id, dataset=__class__._dataset, releases=__class__._releases)
		

class DatasetResolverBase(ABC):
	
	@abstractproperty
	def dataset(self):
		return self._dataset

	@abstractproperty
	def releases(self):
		return NotImplementedError("")

	def resolve_filename_from_id(self, sci_id) -> str:
		return self.resolve_filename_from_release(sci_id=sci_id, dataset=self.dataset, releases=self.releases)

	def resolve_filename_from_release(self, sci_id=None, dataset=None, releases=None) -> str:
		'''
		Given a SciID pointing to a file, return a URL that locates the resource.
		
		:param sci_id:
		:param dataset: the short name of the dataset
		:param releases: list of releases to search for the file under
		'''
		# -----------------------------
		# currently supports [GR6, GR7]
		# -----------------------------
		
		# match format: /file/wise/allsky/filename.ext#fragment
		#print(__class__)
		match = re.search(f"^sciid:/astro/file/{dataset}/({'|'.join(releases)})/(.+)#?(.+)?", sci_id.sciid)
		if match:
			release = match.group(1)
			filename = match.group(2)
			fragment = match.group(3)
			
			params = {
				'dataset' : dataset,
				'release' : release	
			}

			# all GALEX filenames are unique, so we can use the generic filename resolver
			try:
				records = sci_id.resolver.generic_filename_resolver(filename=filename, dataset=dataset, release=release)
			except Exception as e:
				raise NotImplementedError(f"error occurred when calling API: {e}")
				
			logger.debug(f"response: {json.dumps(records, indent=4)}\n")
			if len(records) == 1:
				url = records[0]["url"] # don't set sci_id.url here or will infinitely recurse
				return url
			else:
				raise NotImplementedError(f"Handle case when multiple filename records found: dataset={dataset}, release={release} {records}.")
		
		else:
			print("re: could not match")		
		
		raise exc.UnableToResolveSciIDToURL("The SciID could not be resolved to a URL.")
					