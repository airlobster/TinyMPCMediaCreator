from datetime import datetime, timedelta
import pytz, tzlocal
import time

def from_naive(t=datetime.now(), tzname:str=None):
	tzn = tzname if tzname else tzlocal.get_localzone_name()
	return pytz.timezone(tzn).localize(t)

def measure_time() -> callable:
	t = time.time_ns
	start = t()
	return lambda : timedelta(microseconds=(t() - start) / 1000)
