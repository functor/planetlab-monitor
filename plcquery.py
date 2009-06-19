#!/usr/bin/python


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

def print_fields(obj, fields):
    for f in fields:
        if f in obj:
            print obj[f],
    print ""

def main():

    from monitor import parser as parsermodule
    parser = parsermodule.getParser()

    parser.set_defaults(get=True,
                        type='node',
                        filter=None,
                        fields='node_id,hostname,last_contact'
                        )

    parser.add_option("", "--get", dest="get", action="store_true",
                        help="just get values for object")

    parser.add_option("", "--type", dest="type", metavar="[node|person|site]", 
                        help="object type to query")

    parser.add_option("", "--fields", dest="fields", metavar="key,list,...", 
                        help="a list of keys to display for each object.")

    parser.add_option("", "--filter", dest="filter", metavar="name=value", 
                        help="Filter passed to Get* calls")

    parser.add_option("", "--nodelist", dest="nodelist", metavar="nodelist.txt", 
                        help="A list of nodes to bring out of debug mode.")
    parser.add_option("", "--listkeys", dest="listkeys", action="store_true",
                        help="A list of nodes to bring out of debug mode.")

    #parser = parsermodule.getParser(['defaults'], parser)
    config = parsermodule.parse_args(parser)
    
    if config.nodelist:
        nodelist = utilfile.getListFromFile(config.nodelist)

    if config.get:
        f = parse_filter(config.filter)
        fields = parse_fields(config.fields)

    if config.type == 'node': 
        n = api.GetNodes(f, fields)
        for i in n:
            print_fields(i, fields)

if __name__ == "__main__":
    main()
