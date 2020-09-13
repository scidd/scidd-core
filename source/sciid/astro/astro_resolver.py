
import os
import re
import pdb
import json
from typing import Dict, List, Union

import requests

import sciid
from .. import exc
from ..cache import LocalAPICache
from .dataset.galex import GALEXResolver
from .dataset.wise import WISEResolver
from .dataset.twomass import TwoMASSResolver
from .dataset.sdss import SDSSResolver
from ..logger import sciid_logger as logger

class SciIDAstroResolver(sciid.Resolver):
	'''
	This resolver can translate SciIDs of the "sciid:astro" domain into URLs that point to the specific resource.
	
	This object encapsulates an external service that does the actual translation. By default the service used
	is ``api.trillianverse.org``, but any service that communicates in the same way can be used. The default is sufficient
	most of the time. An example of using an alternative is when a large number of files are locally available where
	it is preferred to use over downloading new external copies.
	
	:param scheme: scheme where the resolver service uses, e.g. "http", "https"
	:param host: the hostname of the resolver service
	:param port: the port number the resolver service is listening on
	'''
	
	def __init__(self, scheme:str="https", host:str=None, port:int=None):
		super().__init__(scheme=scheme, host=host, port=port)
		self.useCache = True
	
	@classmethod
	def defaultResolver(cls):
		'''
		This factory method returns a resolver that is pre-preconfigured with default values designed to be used out of the box (batteries included).
		
		The default service is ``https://api.trillianverse.org``.
		
		The same object will always be returned from this method (pseudo-singleton).
		'''
		if cls._default_instance is None:
			if "SCIID_ASTRO_RESOLVER_HOST" in os.environ:
				host = os.environ["SCIID_ASTRO_RESOLVER_HOST"]
			else:
				host = "api.trillianverse.org"
			
			if "SCIID_ASTRO_RESOLVER_PORT" in os.environ:
				port = os.environ["SCIID_ASTRO_RESOLVER_PORT"]
			else:
				port = 443
			cls._default_instance = cls(host=host, port=port)
		return cls._default_instance
	
	def get(self, path:str=None, params:dict={}, data:dict={}, headers:Dict[str,str]=None) -> Union[Dict,List]:
		'''
		Make a GET call on the Trillian API with the given path and parameters.
		
		:param path: the path of the API to call
		:param params: a dictionary of the parameters to pass to the API
		:param headers: any additional headers to pass to the API
		:returns: JSON response
		:raises: see: https://2.python-requests.org/en/master/api/#exceptions
		'''
		if path is None:
			raise ValueError("A path must be provided to make an API call.")
		
		with requests.Session() as http_session:
			response = http_session.get(self.base_url + path, params=params)
			logger.debug(f"params={params}")
			logger.debug(f"API request URL: '{response.url}'")
			
			try:
				response.raise_for_status()
			except requests.HTTPError as e:
				try:
					err_msg = response.json()["errors"][0]["message"]
				except:
					err_msg = response.json()
				raise exc.TrillianAPIException(f"An error occurred accessing the Trillian API: {err_msg}")
			
			return response.json()
	
	def urlForSciID(self, sci_id:sciid.SciID, verify_resource=False) -> str:
		'''
		This method resolves a SciID into a URL that can be used to retrieve the resource.
		
		:param sci_id: a `sciid.SciID` object
		:param verify_resource: verify that the resource exists at the location returned, raises `sciid.exc.		ResourceUnavailableWhereResolverExpected` exception if not found
		'''

		# match = re.search("^astro:/(data|file)/([^/]+)/(.+)", id_)
		# if match:
		# 	top_level = match.group(1)
		# 	dataset = match.group(2)
		# 	segment = match.group(3)
		
		if isinstance(sci_id, sciid.astro.SciIDAstroData):
			raise NotImplementedError()
		elif isinstance(sci_id, sciid.astro.SciIDAstroFile):
			#print(f"dataset = {sci_id.dataset}")
			dataset = sci_id.dataset.split(".")[0]
			if dataset == "galex":
				url = GALEXResolver().resolveURLFromSciID(sci_id)
			elif dataset == "wise":
				url = WISEResolver().resolveURLFromSciID(sci_id)
			elif dataset == "2mass":
				url = TwoMASSResolver().resolveURLFromSciID(sci_id)
			elif dataset == "sdss":
				url = SDSSResolver().resolveURLFromSciID(sci_id)
			else:
				raise NotImplementedError(f"The dataset '{sci_id.dataset}' does not currently have a resolver associated with it.")
		else:
			raise NotImplementedError(f"Class {type(sci_id)} not handled in {self.__class__}.")
				
		
		# if sci_id.sciid.startswith("sciid:/astro/data/"):
		# 	url = self._url_for_astrodata(sci_id)
		# elif sci_id.sciid.startswith("sciid:/astro/file/"):
		# 	url = self._url_for_astrofile(sci_id)
		
		#print(f"id={sci_id}")
		#print(f"url={url}")
		
		if verify_resource:
			r = requests.head(url)
			if r.status_code != requests.codes.ok:
				raise exc.ResourceUnavailableWhereResolverExpected("The resolver returned a URL, but the resource was not found at that location.")
		return url

	def _url_for_astrofile(self, sci_id) -> str:
		'''
		'''
		# strip leading identifier text:
		resource_path = sci_id.sciid[len("sciid:/astro/file"):]

		raise NotImplementedError()
	
	def _url_for_astrodata(self, sci_id) -> str:
		'''
		'''
		# strip leading identifier text:
		resource_path = sci_id.sciid[len("sciid:/astro/data"):]
		
		raise NotImplementedError()

	def resourceForID(self, sci_id):
		'''
		Resolve the provided "sciid:" identifier and retrieve the resource it points to.
		'''
		url = self.urlForSciID(sci_id)
		
		# todo: fetch data/file for URL
		
		raise NotImplementedError()

	def genericFilenameResolver(self, dataset:str=None, release:str=None, filename:str=None, uniqueid:str=None) -> List[dict]:
		'''
		This method calls the Trillian API to search for a given filename; dataset and release names are optional.
		
		:param dataset: the short name of the dataset
		:param release: the short name of the release
		:param filename: the file name
		:param uniqueid: if filenames are not unique in the dataset, this is an identifier that disambiguates the records for the filename
		'''
		if uniqueid:
			CACHE_KEY = "/".join(["astro:file", str(dataset), str(release), str(filename), str(uniqueid)])
		else:
			CACHE_KEY = "/".join(["astro:file", str(dataset), str(release), str(filename)])

		if self.useCache:
			try:
				results = json.loads(LocalAPICache.defaultCache()[CACHE_KEY])
				logger.debug("API cache hit")
				return results
			except KeyError:
				pass
		
		if ";" in filename:
			pdb.set_trace()
		
		query_parameters = { "filename" : filename }
		if dataset:
			query_parameters["dataset"] = dataset
		if release:
			query_parameters["release"] = release
		if uniqueid:
			query_parameters["uniqueid"] = uniqueid
			logger.debug(f"uniqueid={uniqueid}")
		results = self.get("/astro/data/filename-search", params=query_parameters)
		
		if self.useCache:
			try:
				LocalAPICache.defaultCache()[CACHE_KEY] = json.dumps(results)
			except Exception as e:
				raise e # remove after debugging
				logger.debug(f"Note: exception in trying to save API response to cache: {e}")
				pass
		
		return results





