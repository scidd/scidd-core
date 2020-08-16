
class ValidResolverNotFound(Exception):
	pass

class NoResolverAssignedException(Exception):
	pass

class UnableToResolveSciIDToURL(Exception):
	pass

class ResourceUnavailableWhereResolverExpected(Exception):
	pass

class UnableToResolveFilenameToSciID(Exception):
	pass

class TrillianAPIException(Exception):
	pass

class UnexpectedSciIDFormatException(Exception):
	pass
 
class FileResourceCouldNotBeFound(Exception):
	pass
