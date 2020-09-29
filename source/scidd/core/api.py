
import os
from typing import Dict

import requests

from scidd.core.utilities.designpatterns import singleton

@singleton
class API:
	
	def __init__(self, host:str="api.trillianverse.org", port:int=443):
		
		self.host = host
		self.port = port
		
		if host is None and "SCIDD_API_HOST" in os.environ:
			self.host = os.environ["SCIDD_API_HOST"]
		if port is None and "SCIDD_API_PORT" in os.environ:
			self.port = os.environ["SCIDD_API_PORT"]
		
		if self.host in ["127.0.0.1", "localhost"]:
			self.scheme = "http://" # for development
		else:
			self.scheme = "https://"

	@property
	def base_url(self) -> str:
		'''
		Returns the base URL for the API, e.g. "https://api.trillianverse.org".
		'''
		return f"{self.scheme}{self.host}:{self.port}"

	def get(self, path=None, params=[], headers:dict=None) -> dict:
		'''
		Make a GET call on the SciDD API with the given path and parameters.
		
		:param path: the path of the API to call
		:param params: a dictionary of the parameters to pass to the API
		:param headers: any additional headers to pass to the API
		:returns: JSON response
		:raises: see: https://2.python-requests.org/en/master/api/#exceptions
		'''
		if path is None:
			raise ValueError("A path must be provided to make an API call.")
		
		with requests.Session() as http_session:
		#	try:
			response = http_session.get(self.base_url + path, params=params)
			response.raise_for_status()
		
		return response.json()

	def post(self, path:str=None, params:dict={}, data:dict={}, headers:Dict[str,str]=None) -> dict:
		'''
		Make a POST call on the Trillian API with the given path, parameters, and body.
		
		:param path: the path of the API to call
		:param params: a dictionary of the parameters to pass to the API
		:param data: data to be passed as the body of the call
		:param headers: any additional headers to pass to the API
		:returns: JSON response
		:raises: see: https://2.python-requests.org/en/master/api/#exceptions
		'''
		if path is None:
			raise ValueError("A path must be provided to make an API call.")

		with requests.Session() as http_session:
			response = http_session.post(self.base_url + path, params=params, data=data)

		raise NotImplementedError()
