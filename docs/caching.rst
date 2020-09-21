Caching
=======

This SciDD module automatically handles the caching of downloaded data and file resources; repeated called
to the same resource will be read from the local machine instead of downloaded multiple times. The user
does not need to take any steps to get this functionality. For those interested in customizing this behavior,
read on brave soul.

SciDD identifiers do not specify the location of the resource they point to; they rely on an external
resolver that can translate them to a URL that points to an instance of the data. The resolver typically
comes in the form of an HTTP REST API (but it doesn't have to). Since a script that uses SciDDs will call
the resolver frequently, a caching scheme is useful to speed susbsequent runs of the same script.
This is the role of the cache manager classes. The cache manager stores downloaded data and file resources in a local
directory. It also stores API requests to the resolver and their responses so that subsequent calls can
be replayed locally. Of course, only idempotent responses (i.e. ones that do not change) are stored.

The ``scidd.core`` module comes with a cache manager class, :class:`SciDDCacheManager`. The user should not be
concerned with the specific implementation of the class which may change from version to version. One property
that the user might want to customize is the location of the cache which is set by the :py:attr:`SciDDCacheManagerBase.path`
property. Since data and API caching are lower-level details the cache object does not play a front-facing role in the use of a SciDD.
The normal case is that a default :class:`SciDDCacheManager` instance is automatically created and used. If one
wanted to customize the location of the cache, for example, this code can be added to the start of a script:
 
 .. code-block:: python
 
 	from scidd.core import SciDDCacheManager
	
	default_cache_manager = SciDDCacheManager.defaultManager()
	default_cache_manager.path = "/some/other/path/to/save/cache"

Setting any property of the default cache will impact all future calls.

Users can implement their own caching schemes for custom behavior. For example, the cache location might be selected such that
it can be shared across multiple servers (e.g. in a cloud computing environment). A cache that can potentially have millions
of files might want to specify a custom subdirectory scheme. For example, the caching of astornomical data might be saved
in subdirectories that correlate to their location on the sky as oppsoed to by filename (or similar). This can be accomplished by
subclassing :class:`SciDDCacheManagerBase` and overriding the :py:attr:`SciDDCacheManagerBase.pathWithinCache` method.

Creating A Custom SciDD Cache
-----------------------------

This abstract base class :class:`SciDDCacheManagerBase` is used to customize the behavior of a SciDD cache.
It can be used in one of two ways. First, use it as a superclass.
This is how :class:`SciDDCacheManager` is implemented. An alternate implementation is to use the ``register`` decorator, making
sure to implement the methods :py:attr:`pathWithinCache`, :py:attr:`localAPICache`, and :py:attr:`path` methods. The class
method :py:func:`SciDDCacheManagerBase.conforms_to_interface` can be used to ensure that the custom class property implements the protocol.
This is an example of how it might be done:

.. code-block:: python

	from scidd.core import SciDDCacheManagerBase
	
	@SciDDCacheManagerBase.register
	class MyCustomCache:
        def __init__(self, ...):
            ...
            try:
                SciDDCacheManagerBase.conforms_to_interface(self)
            except TypeError as e:
                raise TypeError(f"This class does not implement the methods required from SciDDCacheManagerBase: {e}")
			
Now ``MyCustomCache`` responds with ``True`` for ``isinstance(x, SciDDCacheManagerBase)``.
