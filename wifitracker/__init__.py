import datetime
import logging
import logging.config
import os.path

from wifitracker.tracker import Storage

__version__ = '0.1.0'

LOGGING_CONF = os.path.join(os.path.dirname(__file__), "logging.conf")
logging.config.fileConfig(LOGGING_CONF)

STORAGE = Storage(threshold=datetime.timedelta(seconds=2))
