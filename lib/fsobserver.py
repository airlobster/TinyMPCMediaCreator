import watchdog
import watchdog.events
import watchdog.observers
from lib.utilities import trace
from PyQt5 import QtCore

class FSObserver:
	class Signals(QtCore.QObject):
		sig_changed = QtCore.pyqtSignal(object)

	class FSHandler(watchdog.events.FileSystemEventHandler):
		def __init__(self, signal):
			super(FSObserver.FSHandler, self).__init__()
			self.signal = signal

		def on_any_event(self, event: watchdog.events.FileSystemEvent):
			self.signal.emit(event)

	def __init__(self, callback:callable):
		self.observer = None
		self.path = None
		self.signals = FSObserver.Signals()
		self.handler = FSObserver.FSHandler(self.signals.sig_changed)
		self.signals.sig_changed.connect(callback)

	def __del__(self):
		self.stop()

	def start(self, path:str, recursive:bool=False):
		if path == self.path:
			return
		if self.observer:
			self.stop()
		if not path:
			return
		trace(f'Start observing {path}')
		self.observer = watchdog.observers.Observer()
		self.observer.schedule(self.handler, path, recursive=recursive)
		self.observer.start()
		self.path = path

	def stop(self):
		if not self.observer:
			trace('No active observer to stop', level='warning')
			return
		trace(f'Stop observing {self.path}')
		self.observer.stop()
		self.observer.join()
		trace(f'Observer {self.path} stopped')
		self.observer = None
		self.path = None
