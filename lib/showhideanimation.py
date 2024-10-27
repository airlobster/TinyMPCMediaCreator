from PyQt5 import QtCore

class WidgetOpenCloseAnimator:
	class Orientation:
		vertical = 'maximumHeight'
		horizontal = 'maximumWidth'

	def __init__(self, widget, *,
			orientation=Orientation.vertical,
			duration:int=1000,
			minValue:int=0,
			maxValue:int=600,
			active:bool=False
			):
		self.widget = widget
		self.orientation = orientation
		self._active = active
		self.minValue = minValue
		self.maxValue = maxValue
		self.anim = QtCore.QPropertyAnimation(self.widget, bytes(self.orientation, 'utf-8'))
		self.anim.setDuration(duration)
		self.anim.setDirection(QtCore.QPropertyAnimation.Direction.Forward)
		self.anim.setStartValue(self.minValue)
		self.anim.setEndValue(maxValue)

	@property
	def active(self) -> bool:
		return self._active

	@active.setter
	def active(self, a:bool) -> None:
		self._active = a
		self.initState()

	def initState(self):
		propSetter = getattr(self.widget, f'set{self.orientation[0].upper()}{self.orientation[1:]}')
		if not self.active:
			self.widget.show()
			propSetter(self.maxValue)
			return
		propSetter(0)

	def animateShow(self, callback:callable=None):
		if not self.active:
			if callable(callback):
				callback()
			return
		self.anim.setDirection(QtCore.QPropertyAnimation.Direction.Forward)
		if callable(callback):
			self.anim.finished.connect(callback)
		self.anim.start(QtCore.QAbstractAnimation.DeletionPolicy.KeepWhenStopped)

	def animateHide(self, callback:callable=None):
		if not self.active:
			if callable(callback):
				callback()
			return
		self.anim.setDirection(QtCore.QPropertyAnimation.Direction.Backward)
		if callable(callback):
			self.anim.finished.connect(callback)
		self.anim.start(QtCore.QAbstractAnimation.DeletionPolicy.KeepWhenStopped)
