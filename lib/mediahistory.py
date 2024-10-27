import os
import re
from datetime import datetime
from lib.utilities import trace, dict2namedtuple

def mediaHistory(path:str, reverse:bool=True) -> list[tuple]:
	def generate():
		infopath = os.path.join(path, '.mpc-media-info')
		if not os.path.isfile(infopath):
			return
		init = lambda: {'mode':None, 'user':None, 'time':None, 'result':None, 'packages':[]}
		with open(infopath, 'rt') as f:
			o = init()
			for line in f:
				stripped = line.rstrip()
				if not stripped:
					if o['mode'] and o['user'] and o['time']:
						o['packages'] = tuple(o['packages'])
						yield dict2namedtuple('MediaAction', o)
					o = init()
				elif stripped.startswith('Created') or stripped.startswith('Updated'):
					try:
						mode,user,time = re.split(r'by|on', stripped)
						o['mode'] = 'update' if mode.lower().strip()=='updated' else 'create'
						o['user'] = user.strip()
						o['time'] = datetime.strptime(time.strip(), '%Y-%m-%dT%H:%M:%S%z')
					except BaseException as x:
						trace(x, level='error')
						continue
				elif stripped == 'complete!':
					o['result'] = 'complete'
				elif stripped == 'aborted!':
					o['result'] = 'error'
				else:
					o['packages'].append(stripped.lstrip())
	return sorted(generate(), key=lambda x:x.time, reverse=reverse)
