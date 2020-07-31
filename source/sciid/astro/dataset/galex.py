
import logging

import sciid
from ...utilities.designpatterns import singleton
from ...logger import sciid_logger as logger
#from ... import exc

from .dataset import DatasetResolverBase

logger = logging.getLogger("sciid")

@singleton
class GALEXResolver(DatasetResolverBase):
	
	@property
	def dataset(self):
		return "galex"
	
	@property
	def releases(self):
		return ["gr6", "gr7"]
