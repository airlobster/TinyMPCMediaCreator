import os
from lib import applogger
from pathlib import Path
from PyQt5 import QtWidgets, uic
from lib.utilities import \
	trace, confirm, isValidPackage, isValidPath, getMediaInfoHtml, delay
from lib.worker import WorkerTypes, WorkersManager, Compile, RemoveSubDirs, EjectDrive
from settingsdlg import SettingsDialog
from lib.fsobserver import FSObserver
from lib.showhideanimation import WidgetOpenCloseAnimator
from settings import AppState, AppParams
from about import WelcomeDialog
from previewdlg import PreviewDialog

class AppWindow(QtWidgets.QMainWindow):
	def __init__(self, app):
		super().__init__()
		uic.loadUi('ui/main.ui', self)
		self.state = AppState()
		self.params = AppParams()
		self.app = app
		self.targetMedia = None
		self.lastExitCode = -1
		self.workers = WorkersManager()
		self.observer = FSObserver(self.onMediaStateChanged)
		self.setWindowTitle(self.app.getBootstrapInfo('title'))
		self.monitorFrameAnimator = \
			WidgetOpenCloseAnimator(self.frameProgress, duration=500, maxValue=200)
		self.firstTime = not self.loadState()
		self.setupWidgets()
		self.params.listen(self.onParamChanged)
		self.params.load()
		self.refreshButtons()

	def postShow(self):
		if self.firstTime:
			self.onAbout()
		self.comboAvailableDrives.start()

	def setupWidgets(self):
		self.monitorFrameAnimator.initState()

		self.menuTinyMPCCreator.setTitle(self.app.getBootstrapInfo('appname'))
		self.labelVersion.setText(self.app.getBootstrapInfo('version'))
		self.labelCopyright.setText(self.app.getBootstrapInfo('copyright'))

		# widgets events
		self.leSearch.textChanged.connect(self.onSearchTextChanged)
		self.listView.signals.filesDropped.connect(self.onFilesDropped)
		self.listView.signals.expansionsSelectionChanged.connect(self.onExpansionSelectionChange)
		self.listView.model().itemChanged.connect(self.refreshButtons)
		self.btnSelectPackages.clicked.connect(self.onSelectPackages)
		self.btnPurgeMedia.clicked.connect(self.onPurgeTargetMedia)
		self.comboAvailableDrives.currentIndexChanged.connect(self.onCurrentMediaChanged)
		self.btnDeleteExpansions.clicked.connect(self.onDeleteExpansions)
		self.btnAbort.clicked.connect(self.workers.abortAll)
		self.btnAudition.clicked.connect(self.onAudition)
		self.btnEjectMedia.clicked.connect(self.onEjectMedia)
		self.btnPreferences.clicked.connect(self.onSettings)

		# menu actions
		self.actionAbout.triggered.connect(self.onAbout)
		self.actionSettings.triggered.connect(self.onSettings)
		self.actionSelect_Packages.triggered.connect(self.onSelectPackages)
		self.actionPurge_media.triggered.connect(self.onPurgeTargetMedia)
		self.action_Delete_selected_expansions.triggered.connect(self.onDeleteExpansions)
		self.action_Refresh.triggered.connect(self.onRefresh)
		self.actionAudition.triggered.connect(self.onAudition)

		self.resetProgressBar()
		self.onRefresh()

	def refreshButtons(self):
		# conditions
		mediaSelected = bool(self.targetMedia)
		mediaIsValid = isValidPath(self.targetMedia)
		workInProgress = bool(self.workers)
		numExpansionsSelected = len(self.listView.selectedExpansions())
		expansionsSelected = numExpansionsSelected != 0
		oneExpansionSelected = numExpansionsSelected == 1

		# widgets
		self.btnSelectPackages.setEnabled(mediaIsValid and not workInProgress)
		self.btnPurgeMedia.setEnabled(mediaIsValid and not workInProgress)
		self.listView.setEnabled(mediaIsValid and not workInProgress)
		self.listView.setAcceptDrops(mediaIsValid and not workInProgress)
		self.btnDeleteExpansions.setEnabled(expansionsSelected)
		self.btnAbort.setEnabled(workInProgress)
		self.progressWorker.setEnabled(workInProgress)
		self.labelMediaLink.setEnabled(mediaIsValid)
		self.btnAudition.setEnabled(oneExpansionSelected)
		self.comboAvailableDrives.setEnabled(not workInProgress)
		self.btnEjectMedia.setEnabled(mediaIsValid and not workInProgress)

		if mediaIsValid:
			self.frameMediaStats.show()
		else:
			self.frameMediaStats.hide()

		# menu
		self.actionSelect_Packages.setEnabled(mediaIsValid and not workInProgress)
		self.actionPurge_media.setEnabled(mediaIsValid and not workInProgress)
		self.action_Delete_selected_expansions.setEnabled(expansionsSelected)
		self.action_Refresh.setEnabled(mediaIsValid)
		self.actionAudition.setEnabled(oneExpansionSelected)

	def closeEvent(self, e):
		confirmType = self.params.ask_before_exit
		if confirmType=='always':
			if not confirm(self, '', 'Are you sure you want to quit?'):
				e.ignore()
				return
		elif confirmType=='if needed' and self.workers:
			if not confirm(self, '', 'Background work is still in progress!\nAre you sure you want to quit?'):
				e.ignore()
				return
		self.workers.abortAll()
		self.workers.waitAll()
		self.observer.stop()
		self.comboAvailableDrives.stop()
		self.app.theme.stop()
		self.params.save()
		self.saveState()
		e.accept()

	def onAbout(self):
		WelcomeDialog(self).open()

	def onRemovableDrivesChanged(self, change):
		self.onRefresh()

	def onSearchTextChanged(self, text):
		self.listView.filter(text)
		self.refreshButtons()

	def onAudition(self):
		selected = self.listView.selectedExpansions()
		if len(selected) != 1:
			return
		PreviewDialog(self, selected[0]).open()

	def onSelectPackages(self):
		filter = " ".join(f"*{e}" for e in self.params.package_extensions)
		packages,_ = QtWidgets.QFileDialog.getOpenFileNames(self,
						caption='Select One or More Packages',
						directory=AppWindow.getInitialFilesSelectionDirectory(),
						filter=f'Compressed files ({filter})'
					)
		if not packages:
			return
		self.onFilesDropped([p for p in packages if isValidPackage(p)])

	def onRefresh(self):
		self.listView.reload()
		self.labelMediaInfo.setText(getMediaInfoHtml(self.targetMedia))

	def onMediaStateChanged(self, ev):
		trace(f'media state changed: {ev}')
		self.onRefresh()
		self.refreshButtons()

	def onParamChanged(self, change):
		if change.name == 'theme':
			self.app.selectTheme(change.value)
		elif change.name == 'thumbnails_size':
			self.listView.imageSize = change.value
		elif change.name == 'monitor_always_visible':
			self.monitorFrameAnimator.active = not change.value
		elif change.name == 'log_level':
			applogger.logger().setLevel(applogger.levelFromName(change.value))
		else:
			trace(f'"{change.name}" change not handled', level='warning')

	def onSettings(self):
		SettingsDialog(self.app, self, self.params).open()

	# user selected a different media from the medias combo
	def onCurrentMediaChanged(self, i):
		trace(f'current media changed: {i}')
		self.setTargetMedia(self.comboAvailableDrives.itemData(i))
		self.refreshButtons()
		self.onRefresh()

	# user has dropped new packages
	def onFilesDropped(self, files):
		trace(f'onFilesDropped: {files}')
		if not isValidPath(self.targetMedia) or bool(self.workers):
			return
		overwrite = self.params.install_overwrite
		self.startJob(Compile(WorkerTypes.WORKER_CREATE,
				self.targetMedia, files, overwrite=overwrite))

	def onEjectMedia(self):
		self.startJob(EjectDrive(WorkerTypes.WORKER_EJECT, self.targetMedia))

	def onDeleteExpansions(self):
		if not isValidPath(self.targetMedia):
			return
		sel = [e for e in self.listView.selectedExpansions()]
		trace(f'selected expansions: {sel}')
		if not sel:
			return
		ask = self.params.ask_before_delete
		if ask == 'always' and not confirm(self, '', f'About to delete {len(sel)} expansion(s)!\nAre you sure?'):
			return
		trace(f'deleting expansions: {sel}')
		self.startJob(RemoveSubDirs(WorkerTypes.WORKER_DELETE, True, *sel))

	def onPurgeTargetMedia(self):
		if not isValidPath(self.targetMedia):
			return
		if not os.listdir(self.targetMedia):
			return # already empty!
		ask = self.params.ask_before_delete
		if ask == 'always' and not confirm(self, '', f'About to delete all contents on this media!\nAre you sure?'):
			return
		trace(f'purging {self.targetMedia}')
		self.startJob(RemoveSubDirs(WorkerTypes.WORKER_PURGE, True,
			os.path.join(self.targetMedia,'Expansions'),
			os.path.join(self.targetMedia,'Samples')
		))

	def onWorkerRead(self, f:callable):
		for line in f():
			trace(line)

	def onWorkerFinished(self, type, exitCode, exitStatus):
		self.lastExitCode = exitCode
		self.workers.remove(type)
		self.listView.reload()
		self.progressWorker.setCompletionFromExitCode(exitCode)
		self.refreshButtons()
		# wait a bit before hiding the monitor area
		delay(self.params.monitor_hide_delay_sec * 1000,
					self.monitorFrameAnimator.animateHide)

	def onProgressInit(self, maxValue:int):
		self.resetProgressBar()
		self.progressWorker.setMaximum(maxValue)
		self.onRefresh()			

	def onProgressIncrement(self, info):
		self.progressWorker.setValue(self.progressWorker.value()+1)
		self.onRefresh()			

	def onExpansionSelectionChange(self):
		self.refreshButtons()

	def setTargetMedia(self, targetMedia):
		if self.targetMedia == targetMedia:
			return
		trace(f'new target media: {targetMedia}')
		self.targetMedia = targetMedia
		self.observer.start(self.targetMedia)
		self.listView.path = self.targetMedia
		self.labelMediaLink.setText(self.targetMedia, 'Show In Finder...')
		self.refreshButtons()

	def loadState(self):
		ret = self.state.load()
		trace(self.state)
		# geometry and window state
		self.setGeometry(*self.state.geometry)
		if self.state.isMaximized:
			self.showMaximized()
		elif self.state.isMinimized:
			self.showMinimized()
		return ret

	def saveState(self):
		self.state.collect(self)
		self.state.save()

	def startJob(self, w):
		w.connect(
			stdout=lambda: self.onWorkerRead(w.readStdout),
			stderr=lambda: self.onWorkerRead(w.readStderr),
			finished=lambda exitCode, exitStatus: self.onWorkerFinished(w.key, exitCode, exitStatus),
			progressInit=self.onProgressInit,
			progressInc=self.onProgressIncrement
		)
		self.workers.add(w)
		self.lastExitCode = -1
		self.resetProgressBar()
		self.refreshButtons()
		self.monitorFrameAnimator.animateShow()
		delay(1000, w.start)

	def resetProgressBar(self):
		self.progressWorker.setMinimum(0)
		self.progressWorker.setMaximum(100)
		self.progressWorker.setValue(0)

	@staticmethod
	def getInitialFilesSelectionDirectory():
		home = Path('~/.').expanduser()
		startDir = home / 'Downloads'
		if not startDir.is_dir():
			startDir = home
		return str(startDir)
