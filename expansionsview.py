import os
import re
from glob import glob
from datetime import datetime
import xml.etree.ElementTree as ET
from PyQt5 import QtWidgets, QtCore, QtGui
from lib.acceptdropfiles import AcceptDroppedFiles
from lib.utilities import trace, isValidPackage
import lib.time

class ImageItem(QtGui.QStandardItem):
	def __init__(self, image_path:str=None, size:int=90):
		super().__init__()
		if image_path:
			self.setData(self.imageFromFilename(image_path, size), QtCore.Qt.DecorationRole)
		else:
			self.setText('-no image-')
			self.setTextAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
			self.setForeground(QtGui.QBrush(QtGui.QColor('gray')))

	def imageFromFilename(self, filename:str, size:int):
		img = QtGui.QPixmap(filename)
		return img.scaled(size, size, QtCore.Qt.KeepAspectRatio)


class ExpansionsModel(QtGui.QStandardItemModel):
	def __init__(self, parent):
		super().__init__(parent)

	def mapToSource(self, index):
		return index


class MultiColumnTextFilterModel(QtCore.QSortFilterProxyModel):
	def __init__(self, parent, columns:list[int]=[1]):
		super().__init__(parent)
		self.pattern = None
		self.inverted = False
		self.columns = columns

	def setPattern(self, pattern, inverted:bool=False):
		self.pattern = pattern.strip() if pattern else None
		self.inverted = inverted

	def filterAcceptsRow(self, source_row, source_parent):
		if not self.pattern:
			return True
		match = self.matchRow(source_row, source_parent)
		return match if not self.inverted else not match

	def matchRow(self, source_row, source_parent):
		for c in self.columns:
			text = self.sourceModel().index(source_row, c, source_parent).data()
			if text and self.pattern.lower() in text.lower():
				return True
		return False


class ExpansionsView(QtWidgets.QTableView, AcceptDroppedFiles):
	imagePadding:int = 2

	class Signals(QtCore.QObject):
		filesDropped = QtCore.pyqtSignal(list)
		expansionsSelectionChanged = QtCore.pyqtSignal()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.signals = ExpansionsView.Signals()
		self.baseModel = ExpansionsModel(self)
		self.setModel(self.baseModel)
		self.expansions = []
		self.pathColumn = -1
		self._imageSize = 90
		self._path = None
		self.selectionModel().selectionChanged.connect(self.onSelectionChanged)
		self.horizontalHeader().setDefaultAlignment(QtCore.Qt.AlignLeft|QtCore.Qt.AlignVCenter)

	@property
	def imageSize(self) -> int:
		return self._imageSize

	@imageSize.setter
	def imageSize(self, size:int):
		self._imageSize = size
		self.horizontalHeader().setDefaultSectionSize(
			size+ExpansionsView.imagePadding*2)
		self.verticalHeader().setDefaultSectionSize(
			size+ExpansionsView.imagePadding*2)
		self.reload()

	@property
	def path(self) -> str:
		return self._path

	@path.setter
	def path(self, p:str):
		self._path = p
		self.reload()

	# notification from selection-model
	def onSelectionChanged(self):
		self.signals.expansionsSelectionChanged.emit()

	# notification from AcceptDroppedFiles.
	def onDroppedFiles(self, files):
		# notify main window
		self.signals.filesDropped.emit(files)

	def dropAllowed(self, f:str) -> bool:
		if not super().dropAllowed(f):
			return False
		return isValidPackage(f)

	def rowCount(self):
		return self.model().rowCount()

	def isEmpty(self):
		self.rowCount() == 0

	def filter(self, pattern):
		def makeFilter():
			m = MultiColumnTextFilterModel(self, columns=[1,2,3])
			m.setSourceModel(self.baseModel)
			m.setPattern(pattern)
			return m
		self.setModel(makeFilter() if pattern.strip() else self.baseModel)
		# reconnect to selection-changed event because this behavior gets lost
		# when switching models
		self.selectionModel().selectionChanged.connect(self.onSelectionChanged)

	def selectedExpansions(self):
		return [
			self.model().mapToSource(i).data()
			for i in self.selectionModel().selectedRows(self.pathColumn)
		]

	def reload(self):
		try:
			self.baseModel.clear()
			self.pathColumn = -1

			if not self.path or not os.path.isdir(self.path):
				return

			self.expansions = list(self.getMediaContentInfo())

			if not self.expansions:
				return

			headers = self.expansions[0]
			self.expansions = sorted(self.expansions[1:], key=lambda x:x[headers.index('title')])

			self.baseModel.setHorizontalHeaderLabels(
				[h.title() if h != 'img' else '' for h in headers])

			# load items from second record
			for row,e in enumerate(self.expansions):
				for col,c in enumerate(e):
					item = ImageItem(c, self.imageSize) \
						if col == headers.index('img') \
						else QtGui.QStandardItem(c)
					self.baseModel.setItem(row,col,item)

			header = self.horizontalHeader()
			self.pathColumn = headers.index('fullpath')
			header.hideSection(self.pathColumn)
			header.setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
			for i in range(1, len(header)):
				header.setSectionResizeMode(i, QtWidgets.QHeaderView.Stretch)
		except BaseException as x:
			trace(x, level='error')

	def getMediaContentInfo(self):
		keys = ['img', 'title', 'manufacturer', 'type', 'time', 'fullpath']
		def scan(path):
			if not os.path.isdir(path):
				return
			for f in os.listdir(path):
				# ignore hidden files and directories
				if f.startswith('.'):
					continue
				try:
					xmlfile = os.path.join(path, f, 'Expansion.xml')
					folderPath = os.path.join(path, f)
					createTime = lib.time.from_naive(datetime.fromtimestamp(
						os.path.getmtime(folderPath))).strftime("%a, %d %b %Y\n%H:%M:%S%z")
					if os.path.isfile(xmlfile):
						xml = ET.parse(xmlfile)
						d = {c.tag:c.text for c in xml.getroot()}
						d = {
								**d,
								'manufacturer': '\n'.join(re.split(r'\s*//\s*', d['manufacturer'])),
								'img':os.path.join(path, f, d['img']),
								'fullpath':folderPath,
								'type':d['type'].title(),
								'time': createTime,
							}
					else:
						d = {
								'img':None,
								'title':f,
								'manufacturer':'',
								'type':'Sample-Pack',
								'fullpath':folderPath,
								'time': createTime,
							}
						# check if there are any wav files there. if not - skip this one
						if not glob('**/*.wav', root_dir=folderPath, recursive=True):
							continue
					yield [d[k] for k in keys]
				except BaseException as x:
					trace(x, level='error')
		if not self.path or not os.path.isdir(self.path):
			return
		yield keys
		yield from scan(os.path.join(self.path, 'Expansions'))
		yield from scan(os.path.join(self.path, 'Samples'))
