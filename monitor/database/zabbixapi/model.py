import pkg_resources
pkg_resources.require("SQLAlchemy>=0.3.10")
pkg_resources.require("Elixir>=0.4.0")
# import the basic Elixir classes and functions for declaring the data model
# (see http://elixir.ematia.de/trac/wiki/TutorialDivingIn)
from elixir import EntityMeta, Entity, Field, OneToMany, ManyToOne, ManyToMany
from elixir import options_defaults, using_options, setup_all, entities
# import some datatypes for table columns from Elixir
# (see http://www.sqlalchemy.org/docs/04/types.html for more)
from elixir import String, Unicode, Integer, DateTime
from sqlalchemy import ColumnDefault
from sqlalchemy import Table
from sqlalchemy.orm import ColumnProperty, object_session

from xml.marshal.generic import Marshaller
from xml.dom.ext import PrettyPrint
from xml.dom.ext.reader.Sax import FromXml
from elementtree import ElementTree

options_defaults['autosetup'] = False

from elixir.statements import Statement
from sqlalchemy import Sequence

import defines

from monitor.database.dborm import zab_metadata, zab_session

__metadata__ = zab_metadata
__session__  = zab_session

# TODO:
#   - declare association between Media and MediaType so that look ups can
#   	occur on 'description'

class ZabbixSerialize(object):

	@classmethod
	def xmlDeserialize(cls, xml):
		d = cls.xml2dict(xml)
		return cls.dict2object(d)

	def xmlSerialize(self, elem=None):
		dict = self.convert_dict(self.to_dict())

		if hasattr(self, 'deepcopy'):
			for val in self.deepcopy:
				dict[val] = getattr(self, val)

		skip_keys = [self._descriptor.auto_primarykey]
		if hasattr(self, 'skip_keys'):
			skip_keys += self.skip_keys

		return self.xmlMessage(dict, skip_keys, elem)

	@classmethod
	def xmlMessage(cls, dict=None, skip_keys=[], use_elem=None):

		elem = ElementTree.Element(cls.classname())

		if isinstance(dict, type({})):
			for key, value in dict.items():
				if key in skip_keys:
					continue

				if isinstance(value, type(0)):
					ElementTree.SubElement(elem, key, type="int").text = str(value)

				elif isinstance(value, type(0L)):
					ElementTree.SubElement(elem, key, type="long").text = str(value)

				elif isinstance(value, type([])):
					if len(value) > 0:
						e = ElementTree.SubElement(elem, key, type="list") 
						for obj in value:
							d = obj.convert_dict(obj.to_dict())
							obj.xmlSerialize(e) 
				else:
					ElementTree.SubElement(elem, key).text = value

		elif isinstance(dict, type([])):
			if len(dict) > 0:
				o = dict[0]
				key = "%s_list" % o.__class__.__name__.lower()
				e = ElementTree.SubElement(elem, key, type="list") 
				for obj in dict:
					d = obj.convert_dict(obj.to_dict())
					obj.xmlSerialize(e) 

		if use_elem is not None:
			use_elem.append(elem)
				
		return ElementTree.tostring(elem)

	@classmethod
	def xml2dict(cls, message, elem=None):
		em = get_zabbix_entitymap()

		if message and elem is None:
			elem = ElementTree.XML(message)
		elif elem is None:
			raise Exception("Cannot proceed with empty xml, and no elem")

		#print "tag: %s : classname : %s" % (elem.tag, cls.classname())
		if cls is not ZabbixSerialize:
			assert elem.tag == cls.classname()
		dict = {}
		for elem in elem:
			if elem.get("type") == "int":
				dict[elem.tag] = int(elem.text)
			elif elem.get("type") == "long":
				dict[elem.tag] = long(elem.text)
			elif elem.get("type") == "list":
				if cls is not ZabbixSerialize:
					assert elem.tag in cls.deepcopy, "List (%s) in XML is not a recognized type for this object (%s)" % (elem.tag, cls.classname())
				dict[elem.tag] = []
				for e in elem:
					dict[elem.tag].append( em[e.tag].xml2dict(None, e) )
			elif elem.text is None:
				dict[elem.tag] = ""
			else:
				dict[elem.tag] = elem.text
		return dict

	@classmethod
	def dict2object(cls, dict):
		em = get_zabbix_entitymap()
		if cls is ZabbixSerialize:
			# note: assume that there's only one type of class
			retdict = {}
			for key in dict.keys():
				clsobj = get_zabbix_class_from_name(key)
				retdict[key] = [ clsobj.dict2object(data) for data in dict[key] ]
			return retdict

		# take deepcopy values out of dict.
		backup = {}
		if hasattr(cls, 'deepcopy'):
			for val in cls.deepcopy:
				if val in dict:
					backup[val] = dict[val]
					del dict[val]

		# instantiate them
		# for each deepcopy object, convert all values in list
		for k in backup.keys():
			clsobj = get_zabbix_class_from_name(k)
			l = [ clsobj.dict2object(data) for data in backup[k] ]
			backup[k] = l

		# find or create the primary object
		obj = cls.find_or_create(**dict)
		#if cls is DiscoveryCheck or \
		#	cls is ActionCondition or \
		#	cls is ActionOperation:
		#	# NOTE: Some objects should always be created. like DiscoveryCheck
		#	obj = None
		#else:
		#	obj = cls.get_by(**dict)
#
#		if obj is None:
#			print "CREATING NEW %s" % cls.classname()
#			obj = cls(**dict)
#		else:
#			print "FOUND EXISTING OBJECT: %s"% obj

		# add deepcopy values to primary object
		for k in backup.keys():
			print type(backup[k][0])

			if isinstance(obj, User) and isinstance(backup[k][0], UsrGrp):
				print "adding groups to user"
				for g in backup[k]:
					obj.append_group(g)

			elif isinstance(obj, User) and isinstance(backup[k][0], Media):
				print "adding media to user"
				for g in backup[k]:
					obj.media_list.append(g)

			elif isinstance(obj, UsrGrp) and isinstance(backup[k][0], HostGroup):
				print "adding hostgroup to usergroup"
				print "NOT IMPLEMENTED!!!"
				for g in backup[k]:
					obj.append_hostgroup(g)
					pass

			elif isinstance(obj, Action) and isinstance(backup[k][0], ActionCondition):
				print "adding actionconditon to action"
				for g in backup[k]:
					obj.actioncondition_list.append(g)

			elif isinstance(obj, Action) and isinstance(backup[k][0], ActionOperation):
				print "adding actionoperation to action"
				for g in backup[k]:
					obj.actionoperation_list.append(g)

			elif isinstance(obj, ActionOperation) and \
				 isinstance(backup[k][0], OperationCondition):
				print "adding operationcondition to actionoperation"
				for g in backup[k]:
					obj.operationcondition_list.append(g)

			elif isinstance(obj, DiscoveryRule) and isinstance(backup[k][0], DiscoveryCheck):
				print "adding discoverycheck to discoveryrule"
				for v in backup[k]:
					obj.discoverycheck_list.append(v)

		return obj

	def convert_dict(self, d):
		rd = {}
		for key in d.keys():
			if type(d[key]) == type([]):
				rd[str(key)] = [ self.convert_dict(v) for v in d[key] ]
			else:
				rd[str(key)] = d[key]
		return rd

	@classmethod
	def classname(cls):
		return cls.__name__

	def prettyserialize(self):
		xml = self.xmlSerialize()
		d = FromXml(xml)
		PrettyPrint(d)
	
class ZabbixEntity(ZabbixSerialize):
	__metaclass__ = EntityMeta

	def __init__(self, **kwargs):
		print "__INIT__ %s" % self.classname()
		tablename = self._descriptor.tablename
		fieldname = self._descriptor.auto_primarykey
		index = IDs.get_by(table_name=tablename, field_name=fieldname)
		if not index:
			index = IDs(table_name=tablename, field_name=fieldname, nodeid=0, nextid=10)
			index.flush()
		index.nextid = index.nextid + 1
		kwargs[fieldname] = index.nextid
		self.set(**kwargs)

	def __repr__(self):
		rd = {}
		if hasattr(self, 'deepcopy'):
			for k in self.deepcopy:
				rd[k] = [ str(v) for v in getattr(self, k) ]

		rd.update(self.to_dict())
		val = ""
		for k in rd.keys():
			val += k
			val += "="
			val += str(rd[k])
			val += ", "
		return self.classname() + "(" + val + ")"

	@classmethod
	def classname(cls):
		return cls.__name__

	def set(self, **kwargs):
		for key, value in kwargs.iteritems():
			setattr(self, key, value)
	
	@classmethod
	def find_or_create(cls, exec_if_new=None, set_if_new={}, **kwargs):
		if cls is DiscoveryCheck or cls is ActionCondition or \
			cls is ActionOperation:
			# NOTE: Some objects should always be created. like DiscoveryCheck
			obj = None
		else:
			# NOTE: ignore *_list items
			query = {}
			for key in kwargs:
				if "_list" not in key:
					query[key] = kwargs[key]
			print "SEARCHING USING %s" % query
			obj = cls.get_by(**query)

		if obj is None:
			print "CREATING NEW %s" % cls.classname()
			print "USING %s" % kwargs
			obj = cls(**kwargs)
			obj.set(**set_if_new)
			if exec_if_new:
				exec_if_new(obj)
		else:
			print "FOUND EXISTING OBJECT: %s"% obj

		return obj

	def update_or_create(cls, data, surrogate=True):
		pk_props = cls._descriptor.primary_key_properties

		# if all pk are present and not None
		if not [1 for p in pk_props if data.get(p.key) is None]:
			pk_tuple = tuple([data[prop.key] for prop in pk_props])
			record = cls.query.get(pk_tuple)
			if record is None:
				if surrogate:
					raise Exception("cannot create surrogate with pk")
				else:
					record = cls()
		else:
			if surrogate:
				record = cls()
			else:
				raise Exception("cannot create non surrogate without pk")
		record.from_dict(data)
		return record
	update_or_create = classmethod(update_or_create)

	def from_dict(self, data):
		"""
		Update a mapped class with data from a JSON-style nested dict/list
		structure.
		"""
		# surrogate can be guessed from autoincrement/sequence but I guess
		# that's not 100% reliable, so we'll need an override

		mapper = sqlalchemy.orm.object_mapper(self)

		for key, value in data.iteritems():
			if isinstance(value, dict):
				dbvalue = getattr(self, key)
				rel_class = mapper.get_property(key).mapper.class_
				pk_props = rel_class._descriptor.primary_key_properties

				# If the data doesn't contain any pk, and the relationship
				# already has a value, update that record.
				if not [1 for p in pk_props if p.key in data] and \
				   dbvalue is not None:
					dbvalue.from_dict(value)
				else:
					record = rel_class.update_or_create(value)
					setattr(self, key, record)
			elif isinstance(value, list) and \
				 value and isinstance(value[0], dict):

				rel_class = mapper.get_property(key).mapper.class_
				new_attr_value = []
				for row in value:
					if not isinstance(row, dict):
						raise Exception(
								'Cannot send mixed (dict/non dict) data '
								'to list relationships in from_dict data.')
					record = rel_class.update_or_create(row)
					new_attr_value.append(record)
				setattr(self, key, new_attr_value)
			else:
				setattr(self, key, value)

	def to_dict(self, deep={}, exclude=[]):
		"""Generate a JSON-style nested dict/list structure from an object."""
		col_prop_names = [p.key for p in self.mapper.iterate_properties \
									  if isinstance(p, ColumnProperty)]
		data = dict([(name, getattr(self, name))
					 for name in col_prop_names if name not in exclude])
		for rname, rdeep in deep.iteritems():
			dbdata = getattr(self, rname)
			#FIXME: use attribute names (ie coltoprop) instead of column names
			fks = self.mapper.get_property(rname).remote_side
			exclude = [c.name for c in fks]
			if isinstance(dbdata, list):
				data[rname] = [o.to_dict(rdeep, exclude) for o in dbdata]
			else:
				data[rname] = dbdata.to_dict(rdeep, exclude)
		return data

	# session methods
	def flush(self, *args, **kwargs):
		return object_session(self).flush([self], *args, **kwargs)

	def delete(self, *args, **kwargs):
		return object_session(self).delete(self, *args, **kwargs)

	def expire(self, *args, **kwargs):
		return object_session(self).expire(self, *args, **kwargs)

	def refresh(self, *args, **kwargs):
		return object_session(self).refresh(self, *args, **kwargs)

	def expunge(self, *args, **kwargs):
		return object_session(self).expunge(self, *args, **kwargs)

	# This bunch of session methods, along with all the query methods below
	# only make sense when using a global/scoped/contextual session.
	def _global_session(self):
		return self._descriptor.session.registry()
	_global_session = property(_global_session)

	def merge(self, *args, **kwargs):
		return self._global_session.merge(self, *args, **kwargs)

	def save(self, *args, **kwargs):
		return self._global_session.save(self, *args, **kwargs)

	def update(self, *args, **kwargs):
		return self._global_session.update(self, *args, **kwargs)

	# only exist in SA < 0.5
	# IMO, the replacement (session.add) doesn't sound good enough to be added
	# here. For example: "o = Order(); o.add()" is not very telling. It's
	# better to leave it as "session.add(o)"
	def save_or_update(self, *args, **kwargs):
		return self._global_session.save_or_update(self, *args, **kwargs)

	# query methods
	def get_by(cls, *args, **kwargs):
		return cls.query.filter_by(*args, **kwargs).first()
	get_by = classmethod(get_by)

	def get(cls, *args, **kwargs):
		return cls.query.get(*args, **kwargs)
	get = classmethod(get)

class IDs(Entity):
	using_options(
		tablename='ids',
		autoload=True,
	)

class Right(ZabbixEntity):
	# rights of a usergroup to interact with hosts of a hostgroup
	using_options(
		tablename='rights',
		autoload=True,
		auto_primarykey='rightid',
	)
	# column groupid is an index to usrgrp.usrgrpid
	# column id is an index into the host-groups.groupid
	# permission is 3=rw, 2=ro, 1=r_list, 0=deny

	# TODO: NOTE: When serialization occurs, the 'permissions' field is lost,
	# currently since the rights table is merely treated as an intermediate
	# table for the m2m between usrgrp and groups.

rights = Table('rights', __metadata__, autoload=True)
hostsgroups = Table('hosts_groups', __metadata__, autoload=True)
hoststemplates = Table('hosts_templates', __metadata__, autoload=True)

	
# m2m table between hosts and groups below
class HostsGroups(ZabbixEntity):
	using_options(
		tablename='hosts_groups',
		autoload=True,
		auto_primarykey='hostgroupid',
	)

class HostsTemplates(ZabbixEntity):
	using_options(
		tablename='hosts_templates',
		autoload=True,
		auto_primarykey='hosttemplateid',
	)

class Host(ZabbixEntity):
	using_options(
		tablename='hosts',
		autoload=True,
		auto_primarykey='hostid',
	)
	hostgroup_list = ManyToMany(
		'HostGroup',
		table=hostsgroups,
		foreign_keys=lambda: [hostsgroups.c.groupid, hostsgroups.c.hostid],
		primaryjoin=lambda: Host.hostid==hostsgroups.c.hostid,
		secondaryjoin=lambda: HostGroup.groupid==hostsgroups.c.groupid,
	)
	template_list = ManyToMany(
		'Host',
		table=hoststemplates,
		foreign_keys=lambda: [hoststemplates.c.hostid, hoststemplates.c.templateid],
		primaryjoin=lambda: Host.hostid==hoststemplates.c.hostid,
		secondaryjoin=lambda: Host.hostid==hoststemplates.c.templateid,
	)

	def append_template(self, template):
		row = HostsTemplates(hostid=self.hostid, templateid=template.hostid)
		return template

	def remove_template(self, template):
		row = HostsTemplates.get_by(hostid=self.hostid, templateid=template.hostid)
		if row is not None:
			row.delete()

	def delete(self):
		# NOTE: media objects are automatically handled.
		hosts_templates_match = HostsTemplates.query.filter_by(hostid=self.hostid).all()
		for row in hosts_templates_match:
			row.delete()

		hosts_groups_match = HostsGroups.query.filter_by(hostid=self.hostid).all()
		for row in hosts_groups_match:
			row.delete()
		super(Host, self).delete()

class HostGroup(ZabbixEntity):
	using_options(
		tablename='groups',
		autoload=True,
		auto_primarykey='groupid',
	)
	usrgrp_list = ManyToMany(
		'UsrGrp',
		table=rights,
		foreign_keys=lambda: [rights.c.groupid, rights.c.id],
		primaryjoin=lambda: HostGroup.groupid==rights.c.id,
		secondaryjoin=lambda: UsrGrp.usrgrpid==rights.c.groupid,
	)
	host_list = ManyToMany(
		'Host',
		table=hostsgroups,
		foreign_keys=lambda: [hostsgroups.c.groupid, hostsgroups.c.hostid],
		primaryjoin=lambda: HostGroup.groupid==hostsgroups.c.groupid,
		secondaryjoin=lambda: Host.hostid==hostsgroups.c.hostid,
	)
	def delete(self):
		# NOTE: media objects are automatically handled.
		hosts_groups_match = HostsGroups.query.filter_by(groupid=self.groupid).all()
		for row in hosts_groups_match:
			row.delete()
		super(HostGroup, self).delete()

class UsersGroups(ZabbixEntity):
	using_options(
		tablename='users_groups',
		autoload=True,
		auto_primarykey='id',
	)

class MediaType(ZabbixEntity):
	using_options(
		tablename='media_type',
		autoload=True,
		auto_primarykey='mediatypeid',
	)

class Script(ZabbixEntity):
	using_options(
		tablename='scripts',
		autoload=True,
		auto_primarykey='scriptid',
	)


# DISCOVERY ################################################3

class DiscoveryCheck(ZabbixEntity):
	using_options(
		tablename='dchecks',
		autoload=True,
		auto_primarykey='dcheckid',
	)
	skip_keys = ['druleid']
	discoveryrule = ManyToOne('DiscoveryRule', 
					primaryjoin=lambda: DiscoveryCheck.druleid == DiscoveryRule.druleid,
					foreign_keys=lambda: [DiscoveryCheck.druleid],
					ondelete='cascade') 

class DiscoveryRule(ZabbixEntity):  # parent of dchecks
	using_options(
		tablename='drules',
		autoload=True,
		auto_primarykey='druleid',
	)
	deepcopy = ['discoverycheck_list']
	discoverycheck_list = OneToMany('DiscoveryCheck', cascade='all, delete-orphan',
					primaryjoin=lambda: DiscoveryCheck.druleid == DiscoveryRule.druleid,
					foreign_keys=lambda: [DiscoveryCheck.druleid])

	discoveredhost_list = OneToMany('DiscoveredHost', cascade='all, delete-orphan',
					primaryjoin=lambda: DiscoveredHost.druleid == DiscoveryRule.druleid,
					foreign_keys=lambda: [DiscoveredHost.druleid])

class DiscoveredHost(ZabbixEntity):
	using_options(
		tablename='dhosts',
		autoload=True,
		auto_primarykey='dhostid',
	)
	discoveryrule = ManyToOne('DiscoveryRule',
					primaryjoin=lambda: DiscoveredHost.druleid == DiscoveryRule.druleid,
					foreign_keys=lambda: [DiscoveredHost.druleid],
					ondelete='cascade') 

	discoveryservice_list = OneToMany('DiscoveryService', cascade='all, delete-orphan',
					primaryjoin=lambda: DiscoveryService.dhostid== DiscoveredHost.dhostid,
					foreign_keys=lambda: [DiscoveryService.dhostid],) 

class DiscoveryService(ZabbixEntity):
	using_options(
		tablename='dservices',
		autoload=True,
		auto_primarykey='dserviceid',
	)
	discoveryrule = ManyToOne('DiscoveredHost',
					primaryjoin=lambda: DiscoveryService.dhostid== DiscoveredHost.dhostid,
					foreign_keys=lambda: [DiscoveryService.dhostid],
					ondelete='cascade') 
						

# ACTIONS ################################################3

class ActionOperation(ZabbixEntity):
	using_options(
		tablename='operations', autoload=True, auto_primarykey='operationid',
	)
	deepcopy = ['operationcondition_list']
	skip_keys = ['actionid']
	action = ManyToOne('Action', ondelete='cascade',
					primaryjoin=lambda: ActionOperation.actionid == Action.actionid,
					foreign_keys=lambda: [ActionOperation.actionid])
					
	operationcondition_list = OneToMany('OperationCondition', cascade='all, delete-orphan',
					primaryjoin=lambda: OperationCondition.operationid == ActionOperation.operationid,
					foreign_keys=lambda: [OperationCondition.operationid])

class OperationCondition(ZabbixEntity):
	using_options(
		tablename='opconditions', autoload=True, auto_primarykey='opconditionid',
	)
	skip_keys = ['operationid']
	actionoperation = ManyToOne('ActionOperation', ondelete='cascade',
					primaryjoin=lambda: OperationCondition.operationid == ActionOperation.operationid,
					foreign_keys=lambda: [OperationCondition.operationid])

class ActionCondition(ZabbixEntity):
	using_options(
		tablename='conditions', autoload=True, auto_primarykey='conditionid',
	)
	skip_keys = ['actionid']
	action = ManyToOne('Action', ondelete='cascade',
					primaryjoin=lambda: ActionCondition.actionid == Action.actionid,
					foreign_keys=lambda: [ActionCondition.actionid])

class Action(ZabbixEntity):
	using_options(
		tablename='actions', autoload=True, auto_primarykey='actionid',
	)
	deepcopy = ['actionoperation_list', 'actioncondition_list']
	actionoperation_list = OneToMany('ActionOperation', cascade='all, delete-orphan',
					primaryjoin=lambda: ActionOperation.actionid == Action.actionid,
					foreign_keys=lambda: [ActionOperation.actionid])
					
	actioncondition_list = OneToMany('ActionCondition', cascade='all, delete-orphan',
					primaryjoin=lambda: ActionCondition.actionid == Action.actionid,
					foreign_keys=lambda: [ActionCondition.actionid])

# USERS & EMAIL MEDIA ################################################3

class Media(ZabbixEntity):
	using_options(
		tablename='media',
		autoload=True,
		auto_primarykey='mediaid',
	)
	skip_keys = ['userid']
	user = ManyToOne('User', 
					primaryjoin=lambda: Media.userid == User.userid,
					foreign_keys=lambda: [Media.userid],
					ondelete='cascade') 

users_groups = Table('users_groups', __metadata__, autoload=True)

class User(ZabbixEntity): # parent of media
	using_options(
		tablename='users',
		autoload=True,
		auto_primarykey='userid',
	)
	deepcopy = ['media_list', 'usrgrp_list']
	media_list = OneToMany('Media', 
					  primaryjoin=lambda: Media.userid == User.userid,
					  foreign_keys=lambda: [Media.userid],
					  cascade='all, delete-orphan')

	# READ-ONLY: do not append or remove groups here.
	usrgrp_list = ManyToMany('UsrGrp',
		  		table=users_groups,
				foreign_keys=lambda: [users_groups.c.userid, users_groups.c.usrgrpid],
				primaryjoin=lambda: User.userid==users_groups.c.userid,
				secondaryjoin=lambda: UsrGrp.usrgrpid==users_groups.c.usrgrpid)

	def delete(self):
		# NOTE: media objects are automatically handled.
		users_groups_match = UsersGroups.query.filter_by(userid=self.userid).all()
		for row in users_groups_match:
			row.delete()
		super(User, self).delete()
		
	def append_group(self, group):
		ug_row = UsersGroups(usrgrpid=group.usrgrpid, userid=self.userid)
		return group

	def remove_group(self, group):
		ug_row = UsersGroups.get_by(usrgrpid=group.usrgrpid, userid=self.userid)
		if ug_row is not None:
			ug_row.delete()
			#ug_row.flush()
		return
		
class UsrGrp(ZabbixEntity):
	using_options(
		tablename='usrgrp',
		autoload=True,
		auto_primarykey='usrgrpid',
	)
	deepcopy= ['hostgroup_list']

	user_list = ManyToMany(
		'User',
		table=users_groups,
		foreign_keys=lambda: [users_groups.c.userid, users_groups.c.usrgrpid],
		secondaryjoin=lambda: User.userid==users_groups.c.userid,
		primaryjoin=lambda: UsrGrp.usrgrpid==users_groups.c.usrgrpid,
	)

	hostgroup_list = ManyToMany(
		'HostGroup',
		table=rights,
		foreign_keys=lambda: [rights.c.groupid, rights.c.id],
		primaryjoin=lambda: UsrGrp.usrgrpid==rights.c.groupid,
		secondaryjoin=lambda: HostGroup.groupid==rights.c.id,
	)

	def delete(self):
		rights_match = Right.query.filter_by(groupid=self.usrgrpid).all()
		for row in rights_match:
			row.delete()

		users_groups_match = UsersGroups.query.filter_by(usrgrpid=self.usrgrpid).all()
		for row in users_groups_match:
			row.delete()

		super(UsrGrp, self).delete()

	def append_hostgroup(self, hg):
		# NOTE: I know it looks wrong, but this is how the keys are mapped.
		print "APPENDING HOSTGROUP %s!!!!!!!!!!" % hg.name
		ug_row = Right(groupid=self.usrgrpid, id=hg.groupid, permission=3)
		ug_row.save()
		return

	def append_user(self, user):
		ug_row = UsersGroups(userid=user.userid, usrgrpid=self.usrgrpid)
		ug_row.save()
		return

	def remove_user(self, user):
		ug_row = UsersGroups.get_by(userid=user.userid, usrgrpid=self.usrgrpid)
		if ug_row is not None:
			ug_row.delete()
			#ug_row.flush()
		return

setup_all()

def get_zabbix_class_from_name(name):
	em = get_zabbix_entitymap()
	cls = None
	if "_list" in name:
		name=name[:-5]	# strip off the _list part.

	for k in em.keys():
		if name == k.lower():
			cls = em[k]
	return cls
	
def get_zabbix_entitymap():
	entity_map = {}
	for n,c in zip([ u.__name__ for u in entities], entities): 
		entity_map[n] = c
	return entity_map

# COMMON OBJECT TYPES
class OperationConditionNotAck(object):
	def __new__(cls):
		o = OperationCondition(
				conditiontype=defines.CONDITION_TYPE_EVENT_ACKNOWLEDGED, 
				operator=defines.CONDITION_OPERATOR_EQUAL, 
				value=0 ) # NOT_ACK
		return  o

#import md5
#u = User(alias="stephen.soltesz@gmail.com", name="stephen.soltesz@gmail.com", surname="", passwd=md5.md5("test").hexdigest(), url="", autologin=0, autologout=900, lang="en_gb", refresh=30, type=1, theme="default.css")
#u.flush()
