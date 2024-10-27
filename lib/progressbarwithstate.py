from PyQt5.QtWidgets import QProgressBar
from lib.customproperty import CustomProperty

class ProgressBarWithState(QProgressBar):
	class States:
		UNKNOWN:str = 'unknown'
		INPROGRESS:str = 'inprogress'
		SUCCESS:str = 'success'
		ERROR:str = 'error'

	formats = {
		States.UNKNOWN: r'',
		States.INPROGRESS: r'%p% completed...',
		States.SUCCESS: r'Success!',
		States.ERROR: r'Failed!'
	}

	def __init__(self, parent):
		super().__init__(parent)
		self._completion = CustomProperty(self, 'completion')
		self.completion = ProgressBarWithState.States.UNKNOWN

	def setValue(self, v):
		super().setValue(v)
		if v == self.minimum():
			self.completion = ProgressBarWithState.States.UNKNOWN
		else:
			self.completion = ProgressBarWithState.States.INPROGRESS

	@property
	def completion(self):
		return self._completion.get()

	@completion.setter
	def completion(self, value:str):
		self.setFormat(ProgressBarWithState.formats[value])
		self._completion.set(value)

	def setCompletionFromExitCode(self, ec:int):
		if ec < 0:
			self.completion = ProgressBarWithState.States.INPROGRESS
		elif ec == 0:
			self.completion = ProgressBarWithState.States.SUCCESS
		else:
			self.completion = ProgressBarWithState.States.ERROR
