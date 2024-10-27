import os
from abc import ABC, abstractmethod
import signal
from PyQt5 import QtCore
from lib.utilities import trace
from lib.time import measure_time


class AbstractSubprocessOutputParser(ABC):
	def __init__(self, parent):
		assert isinstance(parent, BackgroundProcess), \
			f'parent {parent} must be a BackgroundProcess or decendant'
		self.parent = parent

	@abstractmethod
	def parse(self, device:int, chunk:str) -> bool:
		...

###################################################################

class BackgroundProcess():
	class Devices:
		DEV_STDOUT:int = 1
		DEV_STDERR:int = 2

	class ProgressSignals(QtCore.QObject):
		sig_progressInit = QtCore.pyqtSignal(int)
		sig_progressInc = QtCore.pyqtSignal(str)

	def __init__(self, name, command, *args):
		self.signals = BackgroundProcess.ProgressSignals()
		self.exitcode = -1
		self.exitstatus = -1
		self._key = name
		self.command = command
		self.args = list(args)
		self.parsers = []
		self.timefunc = None
		self.lastTimeSpan = None
		trace(f'*command: {self.command}')
		trace(f'*args: {self.args}')
		self.process = QtCore.QProcess()
		# make default connections
		self.process.stateChanged.connect(self.onStateChanged)
		self.process.finished.connect(self.onFinished)
		self.process.readyReadStandardOutput.connect(self.defaultReadStdout)
		self.process.readyReadStandardError.connect(self.defaultReadStderr)
		self.signals.sig_progressInit.connect(lambda total: trace(f'progress: init={total}'))
		self.signals.sig_progressInc.connect(lambda info: trace(f'progress: increment ({info})'))

	@property
	def key(self):
		return self._key

	@property
	def timespan(self):
		return self.lastTimeSpan

	def exitCode(self):
		return (self.exitcode, self.exitstatus)

	def addParser(self, parser:AbstractSubprocessOutputParser) -> None:
		assert isinstance(parser, AbstractSubprocessOutputParser), \
			f'{parser} is an invalid parser object'
		self.parsers.append(parser)

	def start(self) -> None:
		self.exitcode = -1
		self.exitstatus = -1
		self.lastTimeSpan = None
		self.timefunc = measure_time()
		self.process.start(self.command, self.args)

	def abort(self) -> None:
		try:
			pid = self.process.processId()
			trace(f'killing "{self.key}" ({pid})')
			os.kill(pid, signal.SIGINT)
			self.wait()
		except BaseException as x:
			trace(f'kill error: {x}', level='error')

	def wait(self, timeout:int=-1) -> bool:
		return self.process.waitForFinished(timeout)

	def readStdout(self):
		try:
			yield from self.parse(BackgroundProcess.Devices.DEV_STDOUT,
				bytes(self.process.readAllStandardOutput()).decode())
		except Exception as x:
			trace(x, level='error')

	def readStderr(self):
		try:
			yield from self.parse(BackgroundProcess.Devices.DEV_STDERR,
				bytes(self.process.readAllStandardError()).decode())
		except Exception as x:
			trace(x, level='error')

	def connect(self,
			stateChanged:callable=None,
			stdout:callable=None,
			stderr:callable=None,
			finished:callable=None,
			progressInit:callable=None,
			progressInc:callable=None
			):
		if callable(stateChanged):
			self.process.stateChanged.connect(stateChanged)
		if callable(stdout):
			self.process.readyReadStandardOutput.disconnect(self.defaultReadStdout)
			self.process.readyReadStandardOutput.connect(stdout)
		if callable(stderr):
			self.process.readyReadStandardError.disconnect(self.defaultReadStderr)
			self.process.readyReadStandardError.connect(stderr)
		if callable(finished):
			self.process.finished.connect(finished)
		if callable(progressInit):
			self.signals.sig_progressInit.connect(progressInit)
		if callable(progressInc):
			self.signals.sig_progressInc.connect(progressInc)

	def defaultReadStdout(self):
		trace(*self.readStdout())

	def defaultReadStderr(self):
		trace(*self.readStderr())

	def onStateChanged(self, state):
		states = {
			QtCore.QProcess.NotRunning: f'Not running',
			QtCore.QProcess.Starting: 'Starting',
			QtCore.QProcess.Running: 'Running',
		}
		trace(f'Worker "{self.key}" state changed: {states[state]}')

	def onFinished(self, exitCode, exitStatus):
		self.lastTimeSpan = self.timefunc()
		trace(f'Worker "{self.key}" finished: code={exitCode}, status={exitStatus}, time={str(self.timespan)}')
		self.exitcode = exitCode
		self.exitstatus = exitStatus
		self.process.close()
		self.timefunc = None

	def parse(self, device:int, text:str):
		# split into lines
		for l in (l.strip() for l in text.splitlines(False)):
			# hand line to each registered parser,
			# until one accepts it, or no more parsers
			for parser in self.parsers:
				if parser.parse(device, l):
					break
			else:
				# no parser accepted the line, so hand it out
				yield l

###################################################################

class ProgressParser(AbstractSubprocessOutputParser):
	def __init__(self, parent):
		super().__init__(parent)

	def parse(self, device:int, chunk:str) -> bool:
		# @proginit
		if chunk.startswith('@proginit'):
			_,total = chunk.split(maxsplit=1)
			self.parent.signals.sig_progressInit.emit(int(total))
			return True
		# @proginc
		if chunk.startswith('@proginc'):
			_,info = chunk.split(maxsplit=1)
			self.parent.signals.sig_progressInc.emit(info)
			return True
		# unhandled
		return False


class BashScript(BackgroundProcess):
	def __init__(self, name, *args):
		super().__init__(name, '/bin/sh', *args)
		self.addParser(ProgressParser(self))

###################################################################

class Compile(BashScript):
	def __init__(self, name:str,
			  targetMedia:str,
			  sources:list[str],
			  overwrite:bool=False
			):
		args = [
			'scripts/make-mpc-media.sh',
			*(['-w'] if overwrite else []),
			targetMedia,
			*sources
		]
		super().__init__(name, *args)


class RemoveSubDirs(BashScript):
	def __init__(self, name:str, deleteRoot:bool, *subdirs):
		args = [
			'scripts/rmsubdirs.sh',
			*(['-r'] if deleteRoot else []),
			*subdirs
		]
		super().__init__(name, *args)


class EjectDrive(BashScript):
	def __init__(self, name:str, drive:str):
		args = [
			'scripts/eject.sh',
			drive
		]
		super().__init__(name, *args)

###################################################################

class WorkerTypes:
	WORKER_CREATE='create'
	WORKER_PURGE='purge'
	WORKER_DELETE='delete'
	WORKER_EJECT='eject'

class WorkersManager:
	def __init__(self):
		self.wdb = None

	def __getitem__(self, key):
		return self.wdb

	def __bool__(self):
		return self.wdb is not None

	def __len__(self):
		return 1 if self.wdb else 0

	def add(self, worker):
		assert not self.has(worker.key), f'worker "{worker.key}" still in progress'
		self.wdb = worker

	def remove(self, key):
		assert self.has(key), 'Nothing to remove'
		self.wdb = None

	def has(self, key):
		return bool(self.wdb)

	def hasAny(self):
		return bool(self.wdb)

	def get(self, key):
		return self.wdb

	def start(self, key):
		assert self.has(key), 'Nothing to start'
		self.wdb.start()

	def abort(self, key):
		assert self.has(key), 'nothing to abort'
		self.wdb.abort()

	def abortAll(self):
		if bool(self.wdb):
			self.wdb.abort()

	def wait(self, key, timeout=-1):
		if self.has(key):
			self.wdb.wait(timeout)

	def waitAll(self, timeout=-1):
		if self.wdb:
			self.wdb.wait(timeout)
