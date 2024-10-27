from dataclasses import dataclass
from lib.persistentdataclass import PersistentDataClass
from lib.showhideanimation import WidgetOpenCloseAnimator

@dataclass
class AppState(PersistentDataClass):
	geometry:tuple[int] = (100,100,700,500)
	isMaximized:bool = False
	isMinimized:bool = False
	currentDrive:str = ''

	def collect(self, w):
		g = w.geometry()
		self.geometry = (g.x(), g.y(), g.width(), g.height())
		self.isMaximized = w.isMaximized()
		self.isMinimized = w.isMinimized()
		self.currentDrive = w.comboAvailableDrives.currentData()

@dataclass
class AppParams(PersistentDataClass):
	theme:str = 'auto'
	ask_before_exit:str = "if needed"
	ask_before_delete:str = "always"
	install_overwrite:bool = False
	thumbnails_size:int = 90
	monitor_always_visible:bool = True
	monitor_hide_delay_sec:int = 5
	package_extensions:tuple[str] = ('.zip','.xpn')
	log_level:str = 'debug'

