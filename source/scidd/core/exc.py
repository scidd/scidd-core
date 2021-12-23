
class ValidResolverNotFound(Exception):
	pass

class NoResolverAssignedException(Exception):
	pass

class UnableToResolveSciDDToURL(Exception):
	pass

class ResourceUnavailableWhereResolverExpected(Exception):
	pass

class UnableToResolveFilenameToSciDD(Exception):
	pass

class TrillianAPIException(Exception):
	pass

class UnexpectedSciDDFormatException(Exception):
	pass

class FileResourceCouldNotBeFound(Exception):
	pass

class InternetConnectionError(Exception):
	pass

class ErrorInAccessingAPI(Exception):
	pass

