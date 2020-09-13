import logging

import sciid
from ...utilities.designpatterns import singleton
from ...logger import sciid_logger as logger

from .dataset import DatasetResolverBase

logger = logging.getLogger("sciid")

@singleton
class SDSSResolver(DatasetResolverBase):
	
	@property
	def dataset(self):
		return "sdss"
	
	@property
	def releases(self):
		return ["dr16"]
