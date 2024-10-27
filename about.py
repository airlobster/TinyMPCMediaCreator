from lib.modal import ModalDialog
from lib.utilities import bootstrap, readtextfile
from lib.hyperlinklabel import HyperLinkLabel

class WelcomeDialog(ModalDialog):
	def __init__(self, parent):
		super().__init__(templatefile='ui/welcome.ui', parent=parent)
		bts = bootstrap()
		self.label_2.setText(bts.title)
		self.label_3.setText(f'Ver. {bts.version}')
		self.labelUrl.setText(bts.url, title='More information')
		self.btnContinue.clicked.connect(self.close)
		self.pteLicense.setPlainText(readtextfile('LICENSE'))
		self.labelContact.setText(f'mailto:{bts.maintainer_email}', f'Author: {bts.maintainer}')
