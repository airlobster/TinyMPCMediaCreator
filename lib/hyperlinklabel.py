from PyQt5 import QtWidgets, QtCore

class HyperLinkLabel(QtWidgets.QLabel):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.setOpenExternalLinks(True)
		self.setTextFormat(QtCore.Qt.TextFormat.RichText)

	def setText(self, url, title=None):
		s = f'''
			<a href="{url}" {"disabled" if not self.isEnabled() else ""}>
				{title if title else url}
			</a>
			'''
		QtWidgets.QLabel.setText(self, s if url else '')


class FileSystemHyperLinkLabel(HyperLinkLabel):
	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)

	def setText(self, path, title=None):
		s = f'''
			<a href="file://{path}" {"disabled" if not self.isEnabled() else ""}>
				{title if title else path}
			</a>
			'''
		QtWidgets.QLabel.setText(self, s if path else '')
