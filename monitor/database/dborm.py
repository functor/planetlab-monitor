#import pkg_resources
#pkg_resources.require("SQLAlchemy>=0.4.9")
import sqlalchemy
import elixir
import monitor.config as config
elixir.metadata.bind = sqlalchemy.create_engine(config.databaseuri, echo=False)
elixir.session = sqlalchemy.orm.scoped_session(sqlalchemy.orm.sessionmaker(autoflush=True,autocommit=True))

from infovacuum.model import *
