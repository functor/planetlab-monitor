#!/usr/bin/python

import gdata.spreadsheet.text_db
import gdata.spreadsheet.service
import simplejson
import time
import sys

def get_key_for_dbname(gd_client, dbname):
    feed = gd_client.GetSpreadsheetsFeed()
    for i, entry in enumerate(feed.entry):
        if entry.title.text == dbname:
            # get key for this db.
            return feed.entry[i].id.text.rsplit('/', 1)[1]
    return None

def get_worksheet_for_key(gd_client, key, sheetname):
    feed = gd_client.GetWorksheetsFeed(key)
    for i, entry in enumerate(feed.entry):
        if entry.title.text == sheetname:
            # get id for worksheet
            return feed.entry[i].id.text.rsplit('/', 1)[1]
    return None


def get_row_for_update(gd_client, key, wksht_id, date):
    feed = gd_client.GetListFeed(key, wksht_id)
    for i, entry in enumerate(feed.entry):
        #print entry.custom['date'].text
        if date in entry.custom['date'].text:
            e = {}
            for k in entry.custom: e[k] = entry.custom[k].text
            return (i, e)
    return (0, {})


def update_row(gd_client, key, wksht_id, index, row_data):
    feed = gd_client.GetListFeed(key, wksht_id)
    entry = gd_client.UpdateRow( feed.entry[index], row_data)
    if isinstance(entry, gdata.spreadsheet.SpreadsheetsList):
        print 'Updated!'

        
def get_db(client, name):
    db_list = client.GetDatabases(name=name)
    if len(db_list) == 0:
        db = client.CreateDatabase(name)
    else:
        db = db_list[0]
    return db

def get_table(db, table_name, type_list=None):
    try:
        table_list = db.GetTables(name=table_name)
    except:
        table_list = []

    if len(table_list) == 0:
        table = db.CreateTable(table_name, type_list)
    else:
        table = table_list[0]
    return table


def add_record(table, data):
    row = table.AddRecord(data)
    return row

def main():
    from optparse import OptionParser
    parser = OptionParser()
    
    parser.set_defaults(database="MonitorStats",
                        sheet="",
                        labels="date,good,offline,down,online,disabled,failboot,safeboot",
                        values=None,
                        valuelist=None,
                        update=None,
                        email=None,
                        password=None,
                        prefix="",
                        create=False)
    parser.add_option("", "--email", dest="email", help="")
    parser.add_option("", "--password", dest="password", help="")
    parser.add_option("", "--database", dest="database", help="")
    parser.add_option("", "--create", dest="create", action="store_true", help="")
    parser.add_option("", "--sheet",  dest="sheet", help="")
    parser.add_option("", "--labels", dest="labels", help="")
    parser.add_option("", "--values", dest="values", help="")
    parser.add_option("", "--valuelist", dest="valuelist", help="")
    parser.add_option("", "--update", dest="update", help="")
    parser.add_option("", "--prefix", dest="prefix", help="add a prefix to numeric headers")

    (config, args) = parser.parse_args()
    if len(sys.argv) == 1:
        parser.print_help()
        sys.exit(1)

    email = config.email
    password = config.password
    client = gdata.spreadsheet.text_db.DatabaseClient(email, password)
    gd_client = gdata.spreadsheet.service.SpreadsheetsService() # text_db.DatabaseClient(email, password)
    gd_client.email = email
    gd_client.password = password
    gd_client.source = "add-record-1"
    gd_client.ProgrammaticLogin()

    if config.labels:
        config.labels = config.labels.split(',')
    config.labels = [config.labels[0] ] + [ config.prefix + l for l in config.labels[1:] ]

    data_list = []
    if config.values:
        config.values = config.values.replace("+", " ")
        config.values = config.values.split(',')
        data_list = [dict(zip(config.labels, config.values))]
        print data_list

    elif config.valuelist:
        vl_file = open(config.valuelist, 'r')
        for line in vl_file:
            line = line.strip()
            values = line.split(',')
            data_list.append(dict(zip(config.labels, values)))

    if config.update:
        key = get_key_for_dbname(gd_client, config.database)
        wksht_id = get_worksheet_for_key(gd_client, key, config.sheet)
        (index, row_data) = get_row_for_update(gd_client, key, wksht_id, config.update)
        if index == 0 : print "failed to find row!"; sys.exit(1)
        # update values from command-line over existing values from row
        row_data.update( dict(zip(config.labels, config.values)) )
        update_row(gd_client, key, wksht_id, index, row_data)

    else:
        db = get_db(client, config.database)
        table = get_table(db, config.sheet, config.labels)
        for data in data_list:
            print "Adding data: %s" % data
            add_record(table, data)
    #else:
    #    obj = simplejson.load(sys.stdin)
    #    print obj
    #    for o in obj:
    #        sheet = o['sheet']
    #        del o['sheet']
    #        data = dict(zip(config.labels.split(','), config.values.split(',')))
    #        add_record(table, data)
    #        #add_record(config, o, sheet)

if __name__ == '__main__':
    main()
