import pkg_resources
pkg_resources.require("SQLAlchemy>=0.3.10")
pkg_resources.require("Elixir>=0.4.0")
# import the basic Elixir classes and functions for declaring the data model
# (see http://elixir.ematia.de/trac/wiki/TutorialDivingIn)
from elixir import Entity, Field, OneToMany, ManyToOne, ManyToMany
from elixir import options_defaults, using_options, setup_all
# import some datatypes for table columns from Elixir
# (see http://www.sqlalchemy.org/docs/04/types.html for more)
from elixir import String, Unicode, Integer, DateTime

options_defaults['autosetup'] = False


# your data model

# class YourDataClass(Entity):
#     pass


