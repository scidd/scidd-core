
import pytest
import pathlib

from sciid import SciIDCacheManager

@pytest.fixture
def temporary_cache():
	temporary_cache = SciIDCacheManager(path=pathlib.Path(__file__).parent / "sciid_test_cache")
	return temporary_cache
