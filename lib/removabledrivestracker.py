from PyQt5 import QtCore
from lib.fsobserver import FSObserver
from lib.utilities import trace, listRemovableDrives, delay
from collections import namedtuple

class RemovableDrivesTracker(QtCore.QObject):
	class RDTSignals(QtCore.QObject):
		sig_change = QtCore.pyqtSignal(tuple)

	root:str = '/Volumes'

	Change = namedtuple('RemovableDrivesChange', ['current', 'mounted', 'unmounted'])

	def __init__(self, parent):
		super().__init__(parent)
		self.signals = RemovableDrivesTracker.RDTSignals()
		self.observer = FSObserver(self.callbackWrapper)
		self.mountedDrives = RemovableDrivesTracker.listCurrent()
		trace(f'initial existing drives: {self.mountedDrives}')

	def start(self):
		self.observer.start(RemovableDrivesTracker.root)

	def stop(self):
		self.observer.stop()

	def callbackWrapper(self):
		def delayed():
			# create a change object
			current = RemovableDrivesTracker.listCurrent()
			diff = RemovableDrivesTracker.diff(old=self.mountedDrives, new=current)
			change = RemovableDrivesTracker.Change(current=current, mounted=diff[0], unmounted=diff[1])
			trace(change)
			self.signals.sig_change.emit(change)
			self.mountedDrives = current
		delay(1000, delayed)

	def listen(self, slot:callable):
		self.signals.sig_change.connect(slot)

	@staticmethod
	def listCurrent() -> set[str]:
		return tuple(sorted([d.mountpoint for d in listRemovableDrives()]))

	@staticmethod
	def diff(old:tuple[str], new:tuple[str]) -> tuple[tuple[str],tuple[str]]:
		mounted = tuple(set(new) - set(old))
		unmounted = tuple(set(old) - set(new))
		return (mounted, unmounted)
