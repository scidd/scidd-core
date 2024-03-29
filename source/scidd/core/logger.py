
import logging

try:
	import coloredlogs
	colored_logs_available = True
except ImportError:
	colored_logs_available = False

try:
	scidd_logger
except NameError:

	# set up logger

	scidd_logger = logging.getLogger("scidd.core") # create new logger

	# customize output
	# default: coloredlogs.DEFAULT_LOG_FORMAT = '%(asctime)s %(hostname)s %(name)s[%(process)d] %(levelname)s %(message)s'
	log_format = '[%(filename)s:%(lineno)d] %(name)s %(levelname)s %(message)s'

	if colored_logs_available:
		coloredlogs.install(logger=scidd_logger)

		# Use in app as:
		# logger = logging.getLogger('trillian-api')
		# Log with: logger.info("log message")

		# Customize field styles
		#
		# Get default dictionary defining log styles, e.g.
		# {
		#	'asctime': {'color': 'green'},
		#	'hostname': {'color': 'magenta'},
		#	'levelname': {'color': 'black', 'bold': True},
		#	'name': {'color': 'blue'},
		#	'programname': {'color': 'cyan'},
		#	'username': {'color': 'yellow'}
		# }
		#
		field_styles = coloredlogs.DEFAULT_FIELD_STYLES
		# default value = {'hostname': {'color': 'magenta'},
		#				   'programname': {'color': 'cyan'},
		#				   'name': {'color': 'blue'},
		#                  'levelname': {'color': 'black', 'bold': True},
		#				   'asctime': {'color': 'green'}
		#                 }

		# DEBUG
		# -----
		field_styles["levelname"] = {'color': 'yellow', 'bold': True}
		field_styles["name"] = {'color': 'yellow', 'bold': True} # logger name
		coloredlogs.install(level=logging.DEBUG, field_styles=field_styles, fmt=log_format, logger=scidd_logger)

		# INFO
		# ----
		field_styles["levelname"] = {'color': 'yellow', 'bold': True}
		field_styles["name"] = {'color': 'yellow', 'bold': True} # logger name
		coloredlogs.install(level=logging.INFO, field_styles=field_styles, fmt=log_format, logger=scidd_logger)

		# WARNING
		# -------
		field_styles["levelname"] = {'color': 'yellow', 'bold': True}
		field_styles["name"] = {'color': 'yellow', 'bold': True} # logger name
		coloredlogs.install(level=logging.WARNING, field_styles=field_styles, fmt=log_format, logger=scidd_logger)

		# ERROR
		# -----
		field_styles["levelname"] = {'color': 'red', 'bold': False}
		field_styles["name"] = {'color': 'yellow', 'bold': True} # logger name
		coloredlogs.install(level=logging.ERROR, field_styles=field_styles, fmt=log_format, logger=scidd_logger)

		# CRITICAL
		# --------
		field_styles["levelname"] = {'color': 'red', 'bold': True}
		field_styles["name"] = {'color': 'yellow', 'bold': True} # logger name
		coloredlogs.install(level=logging.CRITICAL, field_styles=field_styles, fmt=log_format, logger=scidd_logger)

		#coloredlogs.set_level(logging.DEBUG)
