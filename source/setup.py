
# ==================== sciid =====================

import re
import setuptools
from distutils.core import setup

import numpy as np

def get_property(prop:str, project:str):
	'''
	Read the requested property (e.g. '__version__', '__author__') from the specified Python module.
	Ref: https://stackoverflow.com/a/41110107/2712652
	'''
	result = re.search(r'{}\s*=\s*[\'"]([^\'"]*)[\'"]'.format(prop), open(project + '/__init__.py').read())
	return result.group(1)
	
sources = [] # e.g. C sources
data_files = []
include_dirs = [] #'trillian', np.get_include()]		# -I directories
library_dirs = []			# -L directories
libraries = []		# libraries to include
# equivalent of a bare #define in C source
define_macros = [('NPY_NO_DEPRECATED_API', 'NPY_1_18_API_VERSION')] # warn if using a deprecated NumPy API, defined in numpy/numpyconfig.h
extra_link_args = [] # e.g. ['-framework', 'OpenGL', '-framework', 'GLUT'])

description = ("A Python package for implementing the SciID data identification scheme and resolving data.")

try:
	with open('HISTORY.rst') as history_file:
		history = history_file.read()
except FileNotFoundError:
	history = ""

try:
	with open('README.rst') as readme_file:
		readme = readme_file.read()
except FileNotFoundError:
	readme = ""
	
long_description = f"{readme}\n\n{history}"

# list of classifiers: https://pypi.org/classifiers/
classifiers = [
    "Development Status :: 4 - Beta",
    "License :: Other/Proprietary License (TBD)",
    "Topic :: Scientific/Engineering :: Astronomy",
    "Intended Audience :: Science/Research"
]

exec(open('sciid/core/version.py').read())
setup(
	name = "sciid_core",
	namespace_packages=["sciid"],
	version = __version__,
	description = description,
	long_description = long_description,
	author = "Demitri Muna",
	author_email = "<email>",
	url="https://sciid.org",
	license = "<license>",
    project_urls={
    	"Documentation": "https://sciid.org",
    	"Source Code":"https://github.com/science-identifier/sciid",
    },
	#packages=['sciid'],
	#packages=setuptools.find_packages(),
	packages=setuptools.find_namespace_packages(include=[f"sciid.*"]), # sciid uses native namespaces; see: https://packaging.python.org/guides/packaging-namespace-packages/#native-namespace-packages
	zip_safe=False,
	#include_dirs=['trillian/core', 'trillian/dataset'],
	data_files=data_files,
	python_requires='>=3.6'
)
