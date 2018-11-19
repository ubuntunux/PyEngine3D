import os

from ..Utilities import Logger

log_level = Logger.INFO  # Logger.DEBUG, Logger.MINOR_INFO, Logger.INFO, Logger.WARNING, Logger.ERROR
logger = Logger.getLogger(level=log_level)
