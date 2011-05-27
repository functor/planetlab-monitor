#!/usr/bin/python

from datetime import datetime

from monitor import config
from monitor import database
from monitor.common import Time
import sys 

def main():
    tickets = database.dbLoad("survey_tickets")

#if True:
    #f = open('rt_monitor_data.csv','w')
    queue = int(sys.argv[1])
    exclude = ['monitor']

    f = sys.stdout
    print >>f, "ticket_id,s1,s2,start,lastreply,replies,complete,creator"
    for t in sorted(tickets.keys()):
        ticket_id = 0
        start = datetime(2004,1,1)
        lastreply = datetime.now()
        resolved = 0
        complete = 0
        replies = 1
        creator = ''
        if tickets[t]['queue'] != queue: continue
        for tr in tickets[t]['transactions']:
            # create - ticketid,creator, datecreated, 
            # correspond - creator, datecreated, content
            # status - newvalue = resolved
            if tr['type'] == 'Create':
                start = tr['datecreated']
                creator = tr['creator']
                if complete==0: complete = 1
            elif tr['type'] == 'Correspond':
                if tr['creator'] not in exclude:
                    lastreply = tr['datecreated']
                    replies += 1
                    if complete == 1: complete = 2

            elif tr['type'] == 'Status' and tr['newvalue'] == 'resolved':
                resolved = 1
                if complete == 2: complete = 3

        if replies < 1100:
            if complete in [2,3]: complete = 1
            else: complete = 0
            print >>f, "%s,%s,%s,%s,%s,%s,%s,%s" % (t, start.strftime('%Y-%m-%d'), lastreply.strftime('%Y-%m-%d'), Time.dt_to_ts(start), Time.dt_to_ts(lastreply), replies, complete, creator)
    f.close()

if __name__ == '__main__':
	main()
