#!/usr/bin/plcsh 

# Setup file to be read by bash on startup
c = {'file_owner': 'root', 
        'dest': '/usr/lib/snoopy.so',
        'enabled': True, 
        'file_permissions': '755',
        'source':'PlanetLabConf/histlog/snoopy_so', 
        'always_update': False,
        'file_group': 'root'}

c2 = {'file_owner': 'root', 
        'dest': '/etc/profile.d/histlog_snoopy.sh',
        'enabled': True, 
        'file_permissions': '644',
        'source':'PlanetLabConf/histlog/histlog_sh', 
        'always_update': False,
        'file_group': 'root'}

h = 'planetlab1.cs.stevens-tech.edu'

i = AddConfFile(c);  if h: AddConfFileToNode(i, h)
i = AddConfFile(c2); if h: AddConfFileToNode(i, h)

# This does not cover nodes in FAILBOOT.  The above commands should also be
# added to BootManager so that commands taken by admins are uploaded before
# exec.

c3 = {'file_owner': 'root', 
        'dest': '/etc/cron.d/upload_snoopylog.cron', 
        'enabled': True,
        'file_permissions': '644', 
        'source': 'PlanetLabConf/histlog/upload.cron.php', 
        'always_update': False,
        'file_group': 'root'}

c4 = {'file_owner': 'root', 
        'dest': '/usr/bin/collect_snoopylog.sh', 
        'enabled': True,
        'file_permissions': '750', 
        'source': 'PlanetLabConf/histlog/collect_snoopylog_sh', 
        'always_update': False,
        'file_group': 'root'}

i = AddConfFile(c3);  if h: AddConfFileToNode(i, h)
i = AddConfFile(c4);  if h: AddConfFileToNode(i, h)

