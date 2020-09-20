SciDD Core API Reference
========================

.. module:: sciid.core

This page documents the core SciDD identifier objects. For most users, the class :class:`SciDD` is the only class
that is needed to interact with. The remaining classes allow for customization of caching and resolvers for specific domains
(e.g. ``scidd:/astro/``).

SciDD Objects
-------------

.. autoclass:: SciDD
	:members:
	:undoc-members:
	:inherited-members:
	:show-inheritance:

This subclass of :class:`SciDD` is used when an identifier specifically points to a file resource.
It provides additional properties, methods, and utility that is useful in working with file.
  
.. autoclass:: SciDDFileResource
	:members:
	:undoc-members:
	:inherited-members:
	:show-inheritance:
		  
Cache Objects
-------------

The class :class:`SciIDCacheManagerBase` defines a protocol that must be implemented for any class to be
a SciID cache. The class :class:`SciIDCacheManager` is the provided manager and is used by default. These
classes are only important for those who want to create a custom cache manager.

.. autoclass:: SciIDCacheManagerBase
	:members:
	:undoc-members:
	:inherited-members:
	:show-inheritance:

.. autoclass:: SciIDCacheManager
	:members:
	:undoc-members:
	:inherited-members:
	:show-inheritance:

.. autoclass:: LocalAPICache
	:members:
	:undoc-members:
	:inherited-members:
	:show-inheritance:
   	
SciID Exceptions
----------------

This is a list of custom exceptions used by this module. They are simply pass-through subclasses of :class:`Exception`.

.. automodule:: sciid.core.exc
   :members:
   :show-inheritance:  
   
SciID Resolver
--------------

This class does the low-level work of resolving a SciID into a URL. The class below is an
abstract base class to be used as a superclass for classes that do the actual work.

.. module:: sciid.core

.. autoclass:: Resolver
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:
