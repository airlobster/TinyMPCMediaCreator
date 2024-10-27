from pathlib import Path
from PyQt5 import QtWidgets
from lib.utilities import delay
from lib.customproperty import CustomProperty
from lib.removabledrivestracker import RemovableDrivesTracker
from settings import AppState

class RemovableDrivesSelector(QtWidgets.QComboBox):
	def __init__(self, parent, changedStateDurationSec=2):
		super().__init__(parent=parent)
		self.changedStateDurationSec = changedStateDurationSec
		self.changed = CustomProperty(self, 'changed', False)
		self.removableDrivesTracker = RemovableDrivesTracker(self)
		self.currentTextChanged.connect(self.onSelectionChanged)

	def start(self):
		self.onRemovableDrivesChanged(None)
		self.removableDrivesTracker.listen(self.onRemovableDrivesChanged)
		self.removableDrivesTracker.start()

	def stop(self):
		self.removableDrivesTracker.stop()

	def onSelectionChanged(self, index):
		self.changed.set(True)
		delay(self.changedStateDurationSec*1000, lambda: self.changed.set(False))

	def onRemovableDrivesChanged(self, change):
		if change:
			if change.unmounted:
				# remove all unmounted
				for d in change.unmounted:
					self.removeItem(self.findData(d))
				# select first of what's left
				self.setCurrentIndex(0)
			if change.mounted:
				# add all mounted
				for d in change.mounted:
					self.addItem(Path(d).stem, userData=d)
				# select first mounted
				d = change.mounted[0]
				self.setCurrentIndex(self.findData(d))
		else:
			# initial artificial call: populate list
			state = AppState()
			state.load()
			self.clear()
			currentIndex = -1
			for i,d in enumerate(RemovableDrivesTracker.listCurrent()):
				self.addItem(Path(d).stem, userData=d)
				if d == state.currentDrive:
					currentIndex = i
			self.setCurrentIndex(currentIndex)
