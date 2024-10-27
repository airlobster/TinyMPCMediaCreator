import sys
import json
import logging.config
import logging
from pathlib import Path

class FileHandlerRenew(logging.FileHandler):
	def __init__(self, filename):
		super(FileHandlerRenew, self).__init__(filename, mode='w')

def logFilename():
	with open('bootstrap.json', 'rt') as f:
		bootstrap = json.load(f)
	return \
		Path(bootstrap.get('logsdir', '/tmp')) \
		/ f'{bootstrap["appname"]}.{Path(sys.argv[0]).stem}.log'

def init_logger():
	logging.config.dictConfig({
		'version': 1,
		'root': {
			'handlers': ['console', 'file'],
			'level': 'DEBUG',
		},
		'handlers': {
			'console': {
				'formatter': 'std_out',
				'class': 'logging.StreamHandler',
			},
			'file': {
				'formatter': 'file_out',
				'class': f'{__name__}.FileHandlerRenew',
				'filename': logFilename(),
			}
		},
		'formatters': {
			'std_out': {
				"format": "%(message)s",
				"datefmt":"%d-%m-%Y %I:%M:%S"
			},
			'file_out': {
				"format": "[%(asctime)s] %(levelname)s %(message)s",
				"datefmt":"%d-%m-%Y %I:%M:%S"
			}
		}
	})
	# avoid logging noise from imported module
	logging.getLogger().setLevel(logging.INFO)
	logging.getLogger(__name__).setLevel(logging.DEBUG)

# init_logger()

def logger():
	return logging.getLogger(__name__)

def levelFromName(name:str):
	levels = {
		'not set': logging.NOTSET,
		'debug': logging.DEBUG,
		'info': logging.INFO,
		'warning': logging.WARNING,
		'error': logging.ERROR,
		'critical': logging.CRITICAL
	}
	if name.lower() not in levels:
		return logging.NOTSET
	return levels[name.lower()]
