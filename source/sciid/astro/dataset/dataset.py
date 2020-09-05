
import re
import pdb
import json
from abc import ABC, abstractmethod, abstractproperty

from ... import exc
from ... import SciID
from ...logger import sciid_logger as logger

# class DatasetResolverBaseMeta(type):
# 	@staticmethod
# 	def resolve_filename(sci_id) -> str:
# 		return DatasetResolverBase.resolveFilenameFromRelease(sci_id=sci_id, dataset=__class__._dataset, releases=__class__._releases)
		

class DatasetResolverBase(ABC):
	'''
	
	'''
	@abstractproperty
	def dataset(self):
		return self._dataset

	@abstractproperty
	def releases(self):
		return NotImplementedError("")

	def resolveURLFromSciID(self, sci_id:SciID) -> str:
		#return self.resolveURLFromRelease(sci_id=sci_id, dataset=self.dataset, releases=self.releases)

	#def resolveURLFromRelease(self, sci_id:SciID=None, dataset:str=None, releases:List[str]=None) -> str:
		'''
		Given a SciID pointing to a file, return a URL that locates the resource.
		
		:param sci_id: a SciID object
		'''
		#:param dataset: the short name of the dataset
		#:param releases: list of releases to search for the file under, or ``None`` to search across all
		#'''

		try:
			dataset, release = sci_id.dataset.split(".")
		except ValueError:
			dataset = sci_id.dataset
			release = None

		if ";" in str(sci_id):
			pdb.set_trace()

		records = sci_id.resolver.genericFilenameResolver(dataset=dataset,
														  release=release,
														  filename=sci_id.filename,
														  uniqueid=sci_id.filenameUniqueIdentifier)
		
		if True:

		# match = re.search(f"^sciid:/astro/file/{dataset}/({'|'.join(releases)})/(.+)#?(.+)?", sci_id.sciid)
		# logger.debug("regexp = " + f"^sciid:/astro/file/{dataset}/({'|'.join(releases)})/(.+)#?(.+)?")
		# if match:
		# 	release = match.group(1)
		# 	filename = match.group(2)
		# 	fragment = match.group(3)
		# 	
		# 	if ";" in filename:
		# 		pdb.set_trace()
		# 	
		# 	#try:
		# 	if True:
		# 		records = sci_id.resolver.genericFilenameResolver(dataset=dataset,
		# 														  release=release,
		# 														  filename=sci_id.filename,
		# 														  uniqueid=sci_id.filenameUniqueIdentifier)
		# 	#except Exception as e:
		# 	#	raise NotImplementedError(f"Error occurred when calling API: {e}")
			
			logger.debug(f"response: {json.dumps(records, indent=4)}\n")
			if len(records) == 1:
				url = records[0]["url"] # don't set sci_id.url here or will infinitely recurse
				if sci_id.url is None:
					sci_id._url = url
				return url
			elif len(records) == 0:
				raise NotImplementedError("Handle no records returned from API.")
			else:
				raise NotImplementedError(f"Handle case when multiple filename records found: dataset={dataset}, release={release} {records}.")
		
		else:
			logger.debug("re: could not match")
		
		pdb.set_trace()
		raise exc.UnableToResolveSciIDToURL(f"The SciID could not be resolved to a URL: '{sci_id}'.")
					