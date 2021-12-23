
import os
import json
import logging
import pathlib
from typing import Dict, Union

import requests

from .exc import ErrorInAccessingAPI
from scidd.core.utilities.designpatterns import singleton,SingletonMeta

logger = logging.getLogger("scidd.core")

#@singleton
#class API:
class API(metaclass=SingletonMeta):
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

	def get(self, path:Union[str, pathlib.Path], params:dict=None, headers:dict=None) -> dict:
		'''
		Make a GET call on the SciDD API with the given path and parameters.

		:param path: the path of the API to call
		:param params: a dictionary of the parameters to pass to the API
		:param headers: any additional headers to pass to the API
		:returns: JSON response
		:raises: see: https://2.python-requests.org/en/master/api/#exceptions
		'''
		#if path is None:
		#	raise ValueError("A path must be provided to make an API call.")
		if params is None:
			params = list()

		with requests.Session() as http_session:
			try:
				response = http_session.get(self.base_url + path, params=params)
			except requests.exceptions.ConnectionError as e:
				if "Max retries exceeded" in str(e):
					raise Exception(f"Unable to reach the API server; is the server down?\n{e}")
				else:
					raise e

			status_code = None
			try:
				response.raise_for_status()
			except requests.HTTPError as e:
				status_code = e.response.status_code
				logger.debug(f"HTTP status code={status_code}")

				# "Absorb" the exception so the trace doesn't go all the way down
				# to the requests package, then check for and raise a custom error below.
				pass

			if status_code is None:
				# no error occurred
				pass
			elif status_code == 500: # "Server Error"
				# a problem occurred on the server returning the response
				raise ErrorInAccessingAPI("\n".join([
					f"An error occurred on the server in accessing the API.",
					f"Please contact Demitri Muna <demitri.muna@utsa.edu> with this full error message.",
					f"URL: {response.url}",
					"Response:",
					f"{json.dumps(response.json(), indent=4)}"
				]))
			else:
				raise Exception(f"Unhandled HTTP error status code: {status_code}")

		return response.json()

	def post(self, path:Union[str, pathlib.Path], params:dict=None, data:dict=None, headers:Dict[str,str]=None) -> dict:
		'''
		Make a POST call on the Trillian API with the given path, parameters, and body.

		:param path: the path of the API to call
		:param params: a dictionary of the parameters to pass to the API
		:param data: data to be passed as the body of the call
		:param headers: any additional headers to pass to the API
		:returns: JSON response
		:raises: see: https://2.python-requests.org/en/master/api/#exceptions
		'''
		#if path is None:
		#	raise ValueError("A path must be provided to make an API call.")

		if params is None:
			params = dict()
		if data is None:
			data = dict()
		if headers is None:
			header = dict()

		raise NotImplementedError()

		with requests.Session() as http_session:
			try:
				response = http_session.post(self.base_url + path, params=params, data=data)
			except requests.exceptions.ConnectionError as e:
				if "Max retries exceeded" in str(e):
					raise Exception(f"Unable to reach the API server; is the server down?\n{e}")
				else:
					raise e

			status_code = None
			try:
				response.raise_for_status()
			except requests.HTTPError as e:
				status_code = e.response.status_code
				logger.debug(f"HTTP status code={status_code}")

				# "Absorb" the exception so the trace doesn't go all the way down
				# to the requests package, then check for and raise a custom error below.
				pass

			if status_code is None:
				# no error occurred
				pass
			elif status_code == 500: # "Server Error"
				# a problem occurred on the server returning the response
				raise ErrorInAccessingAPI("\n".join([
					f"An error occurred on the server in accessing the API.",
					f"Please contact Demitri Muna <demitri.muna@utsa.edu> with this full error message.",
					f"URL: {response.url}",
					"Response:",
					f"{json.dumps(response.json(), indent=4)}"
				]))
			else:
				raise Exception(f"Unhandled HTTP error status code: {status_code}")

