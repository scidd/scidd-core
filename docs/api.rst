SciDD Core API Reference
========================

.. module:: scidd.core

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

The class :class:`SciDDCacheManagerBase` defines a protocol that must be implemented for any class to be
a SciDD cache. The class :class:`SciDDCacheManager` is the provided manager and is used by default. These
classes are only important for those who want to create a custom cache manager.

.. autoclass:: SciDDCacheManagerBase
	:members:
	:undoc-members:
	:inherited-members:
	:show-inheritance:

.. autoclass:: SciDDCacheManager
	:members:
	:undoc-members:
	:inherited-members:
	:show-inheritance:

.. autoclass:: LocalAPICache
	:members:
	:undoc-members:
	:inherited-members:
	:show-inheritance:
   	
SciDD Exceptions
----------------

This is a list of custom exceptions used by this module. They are simply pass-through subclasses of :class:`Exception`.

.. automodule:: scidd.core.exc
   :members:
   :show-inheritance:  
   
SciDD Resolver
--------------

This class does the low-level work of resolving a SciDD into a URL. The class below is an
abstract base class to be used as a superclass for classes that do the actual work, e.g.
in conjunction with an external REST API.

.. module:: scidd.core

.. autoclass:: Resolver
   :members:
   :undoc-members:
   :inherited-members:
   :show-inheritance:
