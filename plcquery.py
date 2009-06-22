#!/usr/bin/python


import sys
from monitor.wrapper import plc
api = plc.api

from monitor import config

def parse_fields(fields):
    if fields:
        s = fields.split(",")
        if s == []:
            return None
        else:
            return s
    else:
        return None

def parse_filter(filter):
    if filter:
        s = filter.split("=")
        if len(s) == 2:
            return {s[0] : s[1]}
        else:
            raise Exception("filter format should be name=value")
    else:
        return None

def print_fields(obj, fields, format):
    if format:
        print format % obj
    else:
        for f in fields:
            if f in obj:
                print obj[f],
        print ""

def list_fields(l):
    if len(l) > 0:
        o = l[0]
        for k in o.keys():
            print k
        sys.exit(1)
    else:
        print "no objects returned to list fields"
        sys.exit(1)

def main():

    from monitor import parser as parsermodule
    parser = parsermodule.getParser()

    parser.set_defaults(get=True,
                        type='node',
                        filter=None,
                        fields=None,
                        format=None,
                        listfields=False,
                        withsitename=False,
                        byloginbase=None,
                        byrole=None,
                        )

    parser.add_option("", "--get", dest="get", action="store_true",
                        help="just get values for object")

    parser.add_option("", "--type", dest="type", metavar="[node|person|site]", 
                        help="object type to query")

    parser.add_option("", "--fields", dest="fields", metavar="key,list,...", 
                        help="a list of keys to display for each object.")

    parser.add_option("", "--filter", dest="filter", metavar="name=value", 
                        help="Filter passed to Get* calls")

    parser.add_option("", "--format", dest="format",
                        help="Format string to use to print")

    parser.add_option("", "--byloginbase", dest="byloginbase",
                        help="")
    parser.add_option("", "--byrole", dest="byrole",
                        help="")
    parser.add_option("", "--withsitename", dest="withsitename",
                        action="store_true", help="")

    parser.add_option("", "--nodelist", dest="nodelist", metavar="nodelist.txt", 
                        help="A list of nodes to bring out of debug mode.")
    parser.add_option("", "--listfields", dest="listfields", action="store_true",
                        help="A list of nodes to bring out of debug mode.")

    #parser = parsermodule.getParser(['defaults'], parser)
    config = parsermodule.parse_args(parser)
    
    if config.nodelist:
        nodelist = utilfile.getListFromFile(config.nodelist)

    if config.get:
        f = parse_filter(config.filter)
        fields = parse_fields(config.fields)

    if config.type == 'node': 
        if config.fields is None: 
            fields='node_id,hostname,last_contact',
            fields = parse_fields(config.fields)

        n = api.GetNodes(f, fields)
        if config.listfields: list_fields(n)
        for i in n:
            print_fields(i, fields, config.format)

    if config.type == 'person': 
            
        if config.byloginbase:
            s = api.GetSites({'login_base' : config.byloginbase}, ['person_ids'])
            f = s[0]['person_ids']
        if config.byrole:
            p = api.GetPersons(None, ['person_id', 'roles'])
            p = filter(lambda x: config.byrole in x['roles'], p)
            f = [ x['person_id'] for x in  p ]

        if config.withsitename:
            n = api.GetPersons(f, fields)
            if config.listfields: list_fields(n)
            for i in n:
                sitelist = api.GetSites(i['site_ids'], ['person_ids', 'name'])
                if len(sitelist) > 0:
                    s = sitelist[0]
                    if i['person_id'] in s['person_ids']:
                        i['name'] = s['name']
                        print_fields(i, fields, config.format)
        else:
            n = api.GetPersons(f, fields)
            if config.listfields: list_fields(n)
            for i in n:
                print_fields(i, fields, config.format)

if __name__ == "__main__":
    main()
