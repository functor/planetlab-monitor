#!/usr/bin/python

# Read in the act_* databases and print out a human readable version

import sys
import time
import getopt
import soltesz


def fields_to_html(fields):
	colorMap = { 'PING'  : 'darkseagreen',
				 'NOPING': 'darksalmon',
				 'SSH': 'darkseagreen',
				 'NOSSH': 'indianred',
				 'PCU': 'darkseagreen',
				 'NOPCU': 'lightgrey',
				 'OLDBOOTCD': 'crimson',
				 'DOWN': 'indianred',
				 'ALPHA': 'gold',
				 'ERROR': 'crimson',
				 'PROD': 'darkseagreen',
				 'DEBUG': 'darksalmon',
				 'DEBUG': 'darksalmon',
				 'BOOT': 'lightgreen'}
	r_str = ""
	for f in fields:
		if f in colorMap:
			bgcolor="bgcolor='%s'" % colorMap[f]
		else:
			bgcolor=""
		r_str += "<td nowrap %s>%s</td>" % (bgcolor, f)
	
	return r_str
	
def rtTicketLink(rt_ticket):
	link = """<a href="https://rt.planet-lab.org/Ticket/Display.html?user=guest&pass=guest&id=%s">RT #%s</a>""" % (rt_ticket, rt_ticket)
	return link

def main():

	total_sites = 0
	total_nodes = 0
	total_restored = 0
	total_down = 0

	act_all = soltesz.dbLoad("act_all")
	plcdb_hn2lb = soltesz.dbLoad("plcdb_hn2lb")
	sickdb = {}

	sorted_keys = act_all.keys()
	sorted_keys.sort()
	for nodename in sorted_keys:
		diag_nodelist = act_all[nodename]
		if nodename in plcdb_hn2lb:
			lb = plcdb_hn2lb[nodename]
			if lb not in sickdb:
				sickdb[lb] = {}
			sickdb[lb][nodename] = diag_nodelist

	sorted_keys = sickdb.keys()
	sorted_keys.sort()
	print "<table width=80% border=1>"
	for loginbase in sorted_keys:
		nodedict = sickdb[loginbase]
		sort_nodekeys = nodedict.keys()
		sort_nodekeys.sort()
		print "<tr><td bgcolor=lightblue nowrap>",
		print loginbase,
		print "</td><td colspan=5>&nbsp;</td>",
		print "</tr>"
		total_sites += 1
		for nodename in sort_nodekeys:
			total_nodes += 1
			if len(act_all[nodename]) == 0:
				#print "<tr><td>%s</td>" % (nodename) 
				#print "<td>has no events</td></tr>"
				continue
			else:
				# print just the latest event
				event = act_all[nodename][0]
				fields = []
				fields += [nodename]
				if 'time' in event:
					s_time=time.strftime("%Y/%m/%d %H:%M:%S",
											time.gmtime(event['time']))
					fields += [s_time]
				if 'ticket_id' in event and event['ticket_id'] != "":
					link = rtTicketLink(event['ticket_id'])
					fields += [link]
				else:
					if 'found_rt_ticket' in event and event['found_rt_ticket'] != "":
						link = rtTicketLink(event['found_rt_ticket'])
						fields += [link]
					else:
						fields += ["No Known RT Ticket"]

				if event['action'] == "close_rt":
					total_restored += 1
				else:
					total_down += 1

				for f in ['category', 'action', 'stage', 'info']:
					if 'stage' in f and 'stage' in event and 'stage' in event['stage']:
						# truncate the stage_ part.
						event['stage'] = event['stage'][6:]
					if f in event:
						if type(event[f]) == type([]):
							fields += event[f]
						else:
							fields += [event[f]]
					else:
						fields += ["&nbsp;"]

				print "<tr>",
				print fields_to_html(fields),
				print "</tr>"

	print "</table>"
	print "<table>"
	print "<tr>"
	print "<th>Sites</th>"
	print "<th>Nodes</th>"
	print "<th>Restored</th>"
	print "<th>Down</th>"
	print "</tr>"

	print "<tr>"
	print "<td>%s</td>" % total_sites
	print "<td>%s</td>" % total_nodes
	print "<td>%s</td>" % total_restored
	print "<td>%s</td>" % total_down

	print "</tr>"
	print "</table>"


	
if __name__ == '__main__':
	print "Content-Type: text/html\r\n"
	print "<html><body>\n"
	main()
	print "</body></html>\n"
