.. SciDD documentation master file, created by
   sphinx-quickstart on Sat Sep 19 01:58:55 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

SciDD: Science Data Descriptors
===============================

A SciDD (science data descriptor) is a scheme designed to define data descriptors for scientific data. They describe a specific
resource, be it a data file, a set of data, a data query, or even a single datum. They do not provide any information *where*
the data is; they only describe the data. A "resolver" is required to turn the identifier into a URL to the specific data.
This scheme has parallels to the `digital object identifier (DOI) <http://doi.org>`_ scheme where the main difference is
the granulairty of the identifier: DOIs point to entire data sets or papers, while SciDDs point to files or even single numeric values.
These are examples of SciDDs:

.. code-block::

   scidd:/astro/file/wise/allsky/03121b119-w2-int-1b.fits#1
   scidd:/astro/file/sdss/dr16/frame-g-006073-1-0025.fits

Continue to the links below for a more detailed introduction and concepts. A paper is in preparation.

.. toctree::
   :maxdepth: 1
   
   introduction
   caching
   
API Reference
=============

.. toctree::
   :maxdepth: 4
   
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
