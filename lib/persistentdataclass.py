import sys, os
from abc import ABC
import json
from pathlib import Path
from dataclasses import fields, is_dataclass
from PyQt5 import QtCore
from lib.utilities import trace, bootstrap
from collections import namedtuple

class PersistentDataClass(ABC):
	PropChange = namedtuple('PropChange', ['object', 'name', 'value', 'oldvalue'])

	class PDCSignals(QtCore.QObject):
		sig_attrChanged = QtCore.pyqtSignal(tuple)

	def __post_init__(self):
		assert is_dataclass(self), f'Inheriting from a non-dataclass object is forbidden!'
		self._filename = self.makeConfigFilename()
		self._pdcsignals = PersistentDataClass.PDCSignals()
		self.listen(self.onAttrChanged)

	def __setattr__(self, name, value) -> None:
		prev = getattr(self, name, None)
		if value == prev:
			return
		super().__setattr__(name, value)
		if hasattr(self, '_pdcsignals'):
			change = PersistentDataClass.PropChange(
						self.__class__.__qualname__, name, value, prev)
			self._pdcsignals.sig_attrChanged.emit(change)

	def __repr__(self):
		return f'{self.__class__.__qualname__}{self.fieldsAsDict().items()}'

	@property
	def configfilename(self):
		return self._filename

	def listen(self, slot:callable):
		assert callable(slot), f'Non-callable slot'
		self._pdcsignals.sig_attrChanged.connect(slot)

	def copyFrom(self, other):
		assert other is not None, f'Cannot copy {self.__class__.__name__} from None instance'
		assert self.__class__ is other.__class__, f'Cannot copy from {other.__class__.__name__} to {self.__class__.__name__}. Type mismatch!'
		for k,v in other.fieldsAsDict().items():
			setattr(self, k, v)

	def load(self) -> bool:
		trace(f'loading {self.__class__.__name__} from {self.configfilename}')
		try:
			with open(self.configfilename, 'rt') as f:
				j = json.load(f)
				for k,v in j.items():
					setattr(self, k, tuple(v) if type(v)==list else v)
			return True
		except BaseException as x:
			trace(x, level='error')
			return False

	def save(self) -> bool:
		trace(f'saving {self.__class__.__name__} to {self.configfilename}')
		try:
			with open(self.configfilename, 'wt') as f:
				json.dump(self.fieldsAsDict(), fp=f, indent='\t')
				print(file=f)
			return True
		except BaseException as x:
			trace(x, level='error')
			return False

	def clone(self):
		return type(self)(**self.fieldsAsDict())

	def fieldsAsDict(self):
		return {field.name:getattr(self,field.name) for field in fields(self)}

	def onAttrChanged(self, change):
		trace(change)

	def makeConfigFilename(self) -> str:
		root = Path('~/').expanduser()
		appname = bootstrap().appname
		filename = self.__class__.__name__
		return str(root / f'.{appname}.{filename.lower()}')
