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
        'source':'PlanetLabConf/histlog/histlog_snoopy_sh', 
        'always_update': False,
        'file_group': 'root'}

h = 'planetlab1.cs.stevens-tech.edu'

i = AddConfFile(c)
if h: 
    AddConfFileToNode(i, h)
i = AddConfFile(c2)
if h: 
    AddConfFileToNode(i, h)

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
        'dest': '/usr/bin/collect_log.sh', 
        'enabled': True,
        'file_permissions': '750', 
        'source': 'PlanetLabConf/histlog/collect_log_sh', 
        'always_update': False,
        'file_group': 'root'}

# NOTE: requires sshd_config option: PermitUserEnvironment=yes
c5 = {'file_owner': 'root', 
        'dest': '/root/.ssh/environment', 
        'enabled': True,
        'file_permissions': '644', 
        'source': 'PlanetLabConf/histlog/environment', 
        'always_update': False,
        'file_group': 'root'}

i = AddConfFile(c3)
if h: 
    AddConfFileToNode(i, h)

i = AddConfFile(c4)
if h: 
    AddConfFileToNode(i, h)

i = AddConfFile(c5)
if h: 
    AddConfFileToNode(i, h)


for i in [84, 85, 86]:
    UpdateConfFile(i, {'enabled': False})

