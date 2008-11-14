#import pkg_resources
#pkg_resources.require("SQLAlchemy>=0.4.9")
import sqlalchemy
import elixir
import monitor.config as config

#elixir.metadata.bind = sqlalchemy.create_engine(config.databaseuri, echo=False)
#elixir.session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker(autoflush=True,autocommit=True))
#infovacuum_db = sqlalchemy.MetaData(bind=sqlalchemy.create_engine(config.monitor_dburi, echo=False))
#infovacuum_session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker(autoflush=True,autocommit=True))

zabbix_engine = sqlalchemy.create_engine(config.zabbix_dburi, echo=config.echo)
metadata = sqlalchemy.MetaData()
metadata.bind = zabbix_engine
session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker(autoflush=False,autocommit=True))
elixir.session, elixir.metadata = session, metadata

#from monitor.database.infovacuum.model import *
from monitor.database.zabbixapi.model import *
