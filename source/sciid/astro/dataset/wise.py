
import logging

import sciid
from ...utilities.designpatterns import singleton
from ...logger import sciid_logger as logger
#from ... import exc

from .dataset import DatasetResolverBase

logger = logging.getLogger("sciid")

@singleton
class WISEResolver(DatasetResolverBase):
	
	@property
	def dataset(self):
		return "wise"
	
	@property
	def releases(self):
		return ["allsky"]
	
