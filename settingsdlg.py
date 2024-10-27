import os
import re
from pathlib import Path
from PyQt5 import QtWidgets
from lib.modal import ModalDialog
from lib.applogger import logFilename
from lib.utilities import restoreFactorySettings
from settings import AppState, AppParams

class SettingsDialog(ModalDialog):
	def __init__(self, app, parent, initialParams:object):
		super().__init__(parent=parent, templatefile='ui/settingsdlg.ui')
		self.app = app
		self.params = initialParams
		self.initialParams = initialParams.clone()
		self.populateThemesCombobox()
		self.refreshView()

		# listen for changes
		self.comboAskBeforeExit.currentTextChanged.connect(
			lambda v: self.onChange('ask_before_exit', v.lower()))
		self.comboAskBeforeDelete.currentTextChanged.connect(
			lambda v: self.onChange('ask_before_delete', v.lower()))
		self.comboTheme.currentTextChanged.connect(
			lambda v: self.onChange('theme', v.lower()))
		self.spinThumbnailsSize.valueChanged.connect(
			lambda v: self.onChange('thumbnails_size', v))
		self.checkboxOverwriteExistingExpansions.stateChanged.connect(
			lambda v: self.onChange('install_overwrite', self.checkboxOverwriteExistingExpansions.isChecked()))
		self.checkboxMonitorAlwaysShown.stateChanged.connect(
			lambda v: self.onChange('monitor_always_visible', self.checkboxMonitorAlwaysShown.isChecked()))
		self.leExtensions.textChanged.connect(
			lambda v: self.onChange('package_extensions', tuple(self.extensionsFixup(v))))
		self.spinProgressBarHideDelay.valueChanged.connect(
			lambda v: self.onChange('monitor_hide_delay_sec', v))
		self.comboLogLevel.currentTextChanged.connect(
			lambda v: self.onChange('log_level', v.lower()))
		self.btnFactoryReset.clicked.connect(self.resetApp)

		# listen to the restore-defaults button
		btnRestore = self.buttonBox.button(QtWidgets.QDialogButtonBox.RestoreDefaults)
		btnRestore.clicked.connect(self.restore)

		logfile = Path(logFilename()).absolute()
		self.labelLogfileLink.setText(logfile, logfile.stem)

		self.refreshButtons()

	def accept(self):
		super().accept()

	def reject(self):
		# restore initial params
		self.params.copyFrom(self.initialParams)
		super().reject()

	def onChange(self, key:str, v:any) -> None:
		setattr(self.params, key, v)
		self.refreshButtons()

	def refreshButtons(self):
		self.spinProgressBarHideDelay.setEnabled(
			not self.checkboxMonitorAlwaysShown.isChecked())

	def restore(self):
		self.params.copyFrom(self.initialParams)
		self.refreshView()

	def refreshView(self):
		self.comboAskBeforeExit.setCurrentText(
			self.params.ask_before_exit.title())
		self.comboAskBeforeDelete.setCurrentText(
			self.params.ask_before_delete.title())
		self.comboTheme.setCurrentText(
			self.params.theme.title())
		self.spinThumbnailsSize.setValue(
			self.params.thumbnails_size)
		self.checkboxOverwriteExistingExpansions.setChecked(
			self.params.install_overwrite)
		self.checkboxMonitorAlwaysShown.setChecked(
			self.params.monitor_always_visible)
		self.leExtensions.setText(
			','.join(self.params.package_extensions))
		self.spinProgressBarHideDelay.setValue(
			self.params.monitor_hide_delay_sec)
		self.comboLogLevel.setCurrentText(
			self.params.log_level.title())

	def populateThemesCombobox(self):
		self.comboTheme.clear()
		for theme in self.app.theme.availableThemes():
			self.comboTheme.addItem(theme.title())

	def extensionsFixup(self, extensions:str) -> list[str]:
		def validExtension(e:str) -> bool:
			return bool(re.fullmatch(r'\.\w+', e))
		def fixExtension(e:str) -> str:
			# replace whatever preceeding the extension itself with a dot(.)
			return re.sub(r'^[^\w]+', '.', e).lower()
		# split 
		splitted = [ e for e in re.split(r'[,;\s]+', extensions) ]
		# fix
		fixed = [ fixExtension(e) for e in splitted if e ]
		# filter out improperly formatted extensions
		return [ e for e in fixed if validExtension(e) ]

	def resetApp(self):
		restoreFactorySettings()
