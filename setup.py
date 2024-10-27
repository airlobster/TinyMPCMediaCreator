"""
This is a setup.py script generated by py2applet

Usage:
    python setup.py py2app
"""

from pathlib import Path
from lib.utilities import bootstrap
from glob import glob
from setuptools import setup, find_packages

def collect_python_modules():
	return [ Path(f).stem for f in glob('./*.py')+glob('./lib/*.py') ]

info = bootstrap()

APP = ['main.py']
DATA_FILES = [
	'LICENSE',
	'bootstrap.json',
]
OPTIONS = {
    'iconfile': 'resources/music.icns',
	'resources': [ 'resources', 'scripts', 'ui' ]
}

setup(
	name=info.appname,
	version=info.version,
	app=APP,
	py_modules=collect_python_modules(),
	data_files=DATA_FILES,
	options={'py2app': OPTIONS},
	packages=find_packages(exclude=('.venv','__pycache__')),
	setup_requires=['py2app'],
	author=info.author,
	author_email=info.author_email,
	maintainer_email=info.maintainer_email,
	url=info.url,
)