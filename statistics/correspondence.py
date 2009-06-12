

def dt_mod_range(dt, range=(60*60*24*7)):
	t_stamp = time.mktime(dt.timetuple())
	t_stamp -= (t_stamp % range)
	dt_ret = datetime.datetime.fromtimestamp(t_stamp)
	return dt_ret

SUPPORT =3
MONITOR =22

weekly_bin = {}
c = 0
for ticket in tickets.keys():
	if tickets[ticket]['queue'] != MONITOR: continue
	for t in tickets[ticket]['transactions']:
		if t['type'] == 'Correspond':
			#print t['datecreated'], t['field'], t['oldvalue'], t['type'], t['newvalue'], t['subject']
			k = dt_mod_range(t['datecreated'])
			s_key = k.strftime("%Y-%m-%d")
			if s_key not in weekly_bin: weekly_bin[s_key] = 0
			
			weekly_bin[s_key] += 1
			
		#	c += 1
		#if c > 100 : break;
	#break;

dates = weekly_bin.keys()
dates.sort()
for t in dates:
	print t, ",", weekly_bin[t]

