import os
from glob import glob
import json
from PyQt5 import QtWidgets, QtGui
import qdarktheme
from lib.utilities import trace, bootstrap, getDefaultsFilePath
import lib.progressbarwithstate
import lib.hyperlinklabel
import expansionsview
import removabledrivesselector

class DarkThemeSwitcher():
	def __init__(self, app):
		self.app = app
		self.currentTheme = None
		qdarktheme.enable_hi_dpi()
		try:
			with open('resources/themes.json', 'rt') as f:
				self.themes = json.load(f)
		except BaseException as x:
			trace(x, level='error')
			self.themes = None

	def set(self, theme):
		trace(f'setting theme: {theme}')
		qdarktheme.setup_theme(
			theme=theme,
			custom_colors=self.themes,
			default_theme=self.currentTheme,
			additional_qss=None
		)
		self.currentTheme = theme

	def get(self):
		return self.currentTheme

	def availableThemes(self):
		return sorted(qdarktheme.get_themes())

	def stop(self):
		qdarktheme.stop_sync()

class TinyMPCApp(QtWidgets.QApplication):
	def __init__(self, args=[]):
		self.theme = DarkThemeSwitcher(self)
		super().__init__(args)
		self.setAutoSipEnabled(False)
		self.setWindowIcon(QtGui.QIcon('resources/music.icns'))
		self.loadCustomFonts()
		self.bootstrap = bootstrap()
		self.defaultsFile = getDefaultsFilePath()
		self.selectTheme('auto')
		self.setAppFont(self.bootstrap.font['family'], self.bootstrap.font['pointSize'])

	def getBootstrapInfo(self, key, default=None):
		return getattr(self.bootstrap, key, default)

	def selectTheme(self, theme):
		self.theme.set(theme)

	def currentTheme(self):
		return self.theme.get()

	def setAppFont(self, fontFamily:str, fontSize:int):
		f = QtGui.QFont(fontFamily, pointSize=fontSize)
		self.setFont(f)

		f = self.font()
		trace(f'current app font: "{f.family()}" {f.pointSize()}', level='info')

	def loadCustomFonts(self):
		for ttf in glob('*.ttf', root_dir='resources'):
			abspath = os.path.abspath(os.path.join('resources', ttf))
			id = QtGui.QFontDatabase.addApplicationFont(abspath)
			if id < 0:
				trace(f'Font "{abspath}" failed to load', level='warning')
