import sys, os
from lib.utilities import trace, bootstrap, resetSettings
from app import TinyMPCApp
from mainwindow import AppWindow
import argparse

def run():
	def parseCommandLine(info):
		parser = argparse.ArgumentParser(info.appname)
		parser.add_argument('-V', '--version', action='store_true', default=False)
		parser.add_argument('-i', '--info', action='store_true', default=False)
		parser.add_argument('-r', '--reset', action='store_true', default=False)
		return parser.parse_args(sys.argv[1:])

	trace(os.uname(), level='info')

	try:
		mainWindow = None

		bts = bootstrap()
		trace(f'bootstrap: {bts}', level='info')

		# handle command-line arguments
		cli = parseCommandLine(bts)
		if cli.reset:
			resetSettings()
			return 0
		if cli.version:
			print(bts.version)
			return 0
		if cli.info:
			print(*[
					f'{k}={v}'
					for k,v in sorted(bts._asdict().items(), key=lambda x:x[0])
				],
				sep='\n')
			return 0

		# start app
		app = TinyMPCApp(sys.argv)
		mainWindow = AppWindow(app)
		mainWindow.show()
		mainWindow.postShow()
		return app.exec()
	except Exception as x:
		trace(f'ERROR: {x}', level='error')
		raise x
	finally:
		pass

if __name__ == '__main__':
	sys.exit(run())
