import os
from PyQt5 import QtCore, QtGui
from lib.modal import ModalDialog
from glob import glob
from lib.utilities import trace
import simpleaudio

class PreviewModel(QtGui.QStandardItemModel):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)


class FilterModel(QtCore.QSortFilterProxyModel):
	def __init__(self, parent, sourceModel, pattern=None):
		super().__init__(parent)
		self.setSourceModel(sourceModel)
		self.setPattern(pattern)

	def setPattern(self, pattern, inverted:bool=False):
		self.pattern = pattern.strip() if pattern else None
		self.inverted = inverted

	def filterAcceptsRow(self, source_row, source_parent):
		if not self.pattern:
			return True
		match = self.matchRow(source_row, source_parent)
		return match if not self.inverted else not match

	def matchRow(self, source_row, source_parent):
		text = self.sourceModel().index(source_row, 0, source_parent).data()
		if text and self.pattern.lower() in text.lower():
			return True
		return False


class PreviewDialog(ModalDialog):
	def __init__(self, parent, expansionPath):
		super().__init__(templatefile='ui/preview.ui', parent=parent)
		self.expansionPath = expansionPath
		self.previewsDir = self.locatePreviews()
		self.player = None
		self.baseModel = PreviewModel()
		self.labelExpansionName.setText(os.path.basename(self.expansionPath))
		self.listDemos.setModel(self.baseModel)
		self.listDemos.selectionModel().selectionChanged.connect(self.onSelectionChanged)
		self.btnPlay.clicked.connect(self.playSelection)
		self.btnStop.clicked.connect(self.stopPlaying)
		self.btnClose.clicked.connect(self.close)
		self.leSearch.textChanged.connect(self.onSearchChanged)
		n = self.loadDemos()
		self.onListContentChanged()

	def done(self, *args):
		self.stopPlaying()
		super().done(*args)

	def onSelectionChanged(self):
		autoPlay = self.checkboxAutoPlay.isChecked()
		if autoPlay:
			self.playSelection()

	def onSearchChanged(self, text):
		t = text.strip()
		if t:
			self.listDemos.setModel(FilterModel(self, self.baseModel, t))
		else:
			self.listDemos.setModel(self.baseModel)
		self.onListContentChanged()
		self.listDemos.selectionModel().selectionChanged.connect(self.onSelectionChanged)

	def onListContentChanged(self):
		self.labelNumItems.setText(f'{self.listDemos.model().rowCount()} samples')

	def playSelection(self):
		self.stopPlaying()
		sel = self.getSelectedIndexes()
		if not sel:
			return
		item = self.getSelectedIndexes()[0].data()
		path = os.path.join(self.previewsDir, item)
		try:
			wave = simpleaudio.WaveObject.from_wave_file(path)
			trace(f'playing {path}')
			self.player = wave.play()
		except BaseException as x:
			trace(f'Error playing "{path}": {x}', level='error')

	def stopPlaying(self):
		if not self.player:
			return
		trace('stopping player')
		self.player.stop()
		self.player = None

	def loadDemos(self):
		items = sorted(glob('**/*.wav', root_dir=self.previewsDir, recursive=True), key=lambda e:e.lower())
		for w in items:
			self.baseModel.appendRow(QtGui.QStandardItem(w))
		return len(items)

	def getSelectedIndexes(self):
		return self.listDemos.selectionModel().selection().indexes()

	def locatePreviews(self):
		path = os.path.join(self.expansionPath, '[Previews]')
		if not os.path.isdir(path):
			return self.expansionPath
		return path

