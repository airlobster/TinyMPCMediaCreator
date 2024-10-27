import sys, os
from shutil import copyfile
from pathlib import Path
import zipfile
import io
import math
import json
import imp # (required by psutil)
import psutil
from collections import namedtuple
from contextlib import contextmanager
from lib.applogger import logger, init_logger, levelFromName
from PyQt5 import QtWidgets, QtCore

init_logger()

def trace(*args, level:str='debug'):
	logger().log(levelFromName(level), *args)

@contextmanager
def opentextfile(path:str, mode:str='rt', encoding:str='utf-8'):
	with io.open(path, mode=mode, encoding=encoding) as f:
		yield f

def readtextfile(path:str, encoding:str='utf-8', default:str=None):
	try:
		with opentextfile(path, mode='rt', encoding=encoding) as f:
			return f.read().strip()
	except:
		return default

def dict2namedtuple(name:str, d:dict) -> tuple:
	return namedtuple(name, sorted(list(d.keys())))(**d)

def bootstrap() -> tuple:
	j = json.loads(readtextfile('bootstrap.json'))
	return dict2namedtuple('Bootstrap', j)

def scaledByteSize(nbytes:int, *, base:int=1000, precision:int=2) -> tuple[float,str]:
	suffixes = ['B', 'Kb', 'Mb', 'Gb', 'Tb', 'Pb']
	if nbytes==0:
		return '0B'
	exp = min(math.floor(math.log(nbytes, base)), len(suffixes)-1)
	return (round(nbytes / base**exp, precision), suffixes[exp])

def listRemovableDrives():
	for d in psutil.disk_partitions():
		if not d.mountpoint.startswith('/Volumes/'):
			continue
		if d.fstype != 'exfat':
			continue
		yield d

def getPathAsPartition(path:str) -> bool:
	try:
		return [dp for dp in psutil.disk_partitions(all=True) if dp.mountpoint==path][0]
	except:
		return None

def getMediaInfo(path:str) -> object:
	try:
		comments = []

		di = getPathAsPartition(path)
		if not di:
			path = '/'
			di = getPathAsPartition(path)
			if not di:
				raise Exception('Warning:\nSelected media is not a valid device!')
		du = psutil.disk_usage(path)

		if di.fstype.lower() != 'exfat':
			comments += ['This device is incompatible with MPC (should be formatted as ExFAT).']

		return dict2namedtuple('DiskInfo', {
				'file_system':di.fstype.upper(),
				'device':di.device,
				'mount_point':di.mountpoint,
				'total_bytes':scaledByteSize(du.total),
				'used_bytes':scaledByteSize(du.used),
				'used_proc':du.used*100/du.total if du.total else 0,
				'free_bytes':scaledByteSize(du.free),
				'free_proc':du.free*100/du.total if du.total else 0,
				'comments': comments,
			})
	except BaseException as x:
		return dict2namedtuple('DiskInfo', {
				'file_system':None,
				'device':None,
				'mount_point':None,
				'total_bytes':None,
				'used_bytes':None,
				'used_proc':None,
				'free_bytes':None,
				'free_proc':None,
				'comments': [str(x)],
			})

def getMediaInfoHtml(path:str):
	info = getMediaInfo(path)
	return f'''
	<html>
		<style>
			.comment {{
				color: orangered;
			}}
		</style>
		<body>
			<b>File-System:</b><span>{info.file_system}</span>
			<b>Capacity:</b><span>{info.total_bytes[0]}{info.total_bytes[1]}<span>
			<b>Free:</b><span>{info.free_bytes[0]}{info.free_bytes[1]}({info.free_proc:.1f}%)<span>
			<b>Used:</b><span>{info.used_bytes[0]}{info.used_bytes[1]}({info.used_proc:.1f}%)<span>
			<b>Comments:</b><span class="comment"> {'<br>'.join(info.comments)}<span>
		</body>
	</html>
	'''

def getDefaultsFilePath():
	return str(Path('~/.').expanduser() / f'.{bootstrap().appname}')

def confirm(parent, title:str, msg:str) -> bool:
	return QtWidgets.QMessageBox.question(parent, title, msg) == QtWidgets.QMessageBox.Yes

def isValidPackage(path:str, extensions:list[str]=['.zip', '.xpn', '.wav']):
	try:
		if not zipfile.is_zipfile(path):
			return False
		with zipfile.ZipFile(path, 'r') as z:
			for e in z.namelist():
				trace(f'{e}?')
				if Path(e).suffix.lower() in extensions:
					return True
	except BaseException as x:
		trace(x, level='error')
	return False

def isValidPath(path):
	return bool(path) \
		and os.access(path, os.R_OK | os.W_OK | os.X_OK | os.F_OK)

def delay(ms:int, slot:callable):
	QtCore.QTimer.singleShot(ms, slot if callable(slot) else lambda:0)

def restart():
	os.execl(sys.executable, os.path.abspath(sys.argv[0]), *sys.argv)

def resetSettings():
	from settings import AppState, AppParams
	stateFile = AppState().configfilename
	paramsFile = AppParams().configfilename
	# save a copy of both files
	copyfile(stateFile, stateFile+'.old')
	copyfile(paramsFile, paramsFile+'.old')
	# delete both files
	os.unlink(stateFile)
	os.unlink(paramsFile)

def restoreFactorySettings():
	trace('Restore factory settings!', level='info')
	resetSettings()
	restart()
