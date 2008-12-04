import sqlalchemy
import elixir
import monitor.config as config

mon_metadata = sqlalchemy.MetaData()
mon_metadata.bind = sqlalchemy.create_engine(config.monitor_dburi, echo=config.echo)
mon_session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker(autoflush=False,autocommit=True))

zab_metadata = sqlalchemy.MetaData()
zab_metadata.bind = sqlalchemy.create_engine(config.zabbix_dburi, echo=config.echo)
zab_session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker(autoflush=False,autocommit=True))
zab_session.bind = zab_metadata.bind
