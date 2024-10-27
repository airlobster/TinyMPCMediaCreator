import os
from PyQt5 import QtCore
from lib.utilities import trace

class AcceptDroppedFiles:
	def __init__(self):
		self.setAcceptDrops(True)

	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.acceptProposedAction()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		if event.mimeData().hasUrls():
			event.acceptProposedAction()
		else:
			event.ignore()

	def dropEvent(self, event):
		# recursive validation
		def dig(path):
			if os.path.isdir(path):
				for f in os.listdir(path):
					yield from dig(os.path.join(path, f))
			elif self.dropAllowed(path):
				trace(f'drop: "{path}" accepted')
				yield path
			else:
				trace(f'drop: "{path}" rejected', level='warning')
		def digIter(it):
			for f in it:
				yield from dig(f)
		md = event.mimeData()
		if not md.hasUrls():
			return
		# convert urls to file paths and filter out the invalid ones
		files = list(digIter(url.toLocalFile() for url in md.urls()))
		if not files:
			return
		event.acceptProposedAction()
		self.onDroppedFiles(files)

	# may be overriden for more precise validation
	def dropAllowed(self, f:str) -> bool:
		return self.acceptDrops()

	# should be overloaded
	def onDroppedFiles(self, files):
		pass
