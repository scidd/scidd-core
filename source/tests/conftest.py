
import pytest
import pathlib

from scidd import SciDDCacheManager

@pytest.fixture
def temporary_cache():
	temporary_cache = SciDDCacheManager(path=pathlib.Path(__file__).parent / "scidd_test_cache")
	return temporary_cache
