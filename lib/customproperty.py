from PyQt5 import QtCore

class CustomProperty(QtCore.QObject):
	def __init__(self, parent, name:str, defaultValue:any=None):
		super().__init__(parent)
		self.propname = name
		self.set(defaultValue)

	def name(self) -> str:
		return self.propname

	def get(self) -> any:
		return self.parent().property(self.propname)

	def set(self, value:any) -> None:
		self.parent().setProperty(self.propname, value)
		self.parent().style().polish(self.parent())
