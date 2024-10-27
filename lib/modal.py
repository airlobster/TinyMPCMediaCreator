from PyQt5 import QtWidgets, uic
from lib.utilities import trace

class ModalDialog(QtWidgets.QDialog):
	def __init__(self, templatefile, parent, flags=[]):
		super().__init__(parent)
		uic.loadUi(templatefile, self)
		self.setModal(True)
		for f in flags:
			self.setWindowFlag(f, True)

	def open(self):
		self.show()
		return self.exec()
