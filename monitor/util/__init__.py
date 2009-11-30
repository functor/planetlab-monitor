
import time
import math

# import local file.py
import file

def diff_time(timestamp, abstime=True):
	now = time.time()
	if timestamp == None:
		return "unknown"
	if abstime:
		diff = now - timestamp
	else:
		diff = timestamp
	# return the number of seconds as a difference from current time.
	t_str = ""
	if diff < 60: # sec in min.
		t = diff / 1
		t_str = "%s sec ago" % int(math.ceil(t))
	elif diff < 60*60: # sec in hour
		t = diff / (60)
		t_str = "%s min ago" % int(math.ceil(t))
	elif diff < 60*60*24: # sec in day
		t = diff / (60*60)
		t_str = "%s hrs ago" % int(math.ceil(t))
	elif diff < 60*60*24*14: # sec in week
		t = diff / (60*60*24)
		t_str = "%s days ago" % int(math.ceil(t))
	elif diff <= 60*60*24*30: # approx sec in month
		t = diff / (60*60*24)
		t_str = "%s days ago" % int(math.ceil(t))
	elif diff > 60*60*24*30: # approx sec in month
		t = diff / (60*60*24*30)
		t_str = "%s mnths ago" % int(t)
	return t_str
