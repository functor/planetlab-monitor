from elixir import Entity, Field, OneToMany, ManyToOne, ManyToMany
from elixir import options_defaults, using_options, setup_all, belongs_to
from elixir import String, Integer as Int, DateTime, PickleType, Boolean
from datetime import datetime,timedelta
import elixir
import traceback
from elixir.ext.versioned import *
from pcucontrol import reboot

from monitor.database.dborm import mon_metadata, mon_session
__metadata__ = mon_metadata
__session__  = mon_session


class FindbadNodeRecord(Entity):
	@classmethod
	def get_all_latest(cls):
		return cls.query.all()

	@classmethod
	def get_latest_by(cls, **kwargs):
		return cls.query.filter_by(**kwargs).first()

	@classmethod
	def get_latest_by(cls, **kwargs):
		return cls.query.filter_by(**kwargs).first()

	@classmethod
	def get_latest_n_by(cls, n=3, **kwargs):
		return cls.query.filter_by(**kwargs)

# ACCOUNTING
	date_checked = Field(DateTime,default=datetime.now)
	round = Field(Int,default=0)
	hostname = Field(String,primary_key=True,default=None)
	loginbase = Field(String)

# INTERNAL
	kernel_version = Field(String,default=None)
	bootcd_version = Field(String,default=None)
        boot_server = Field(String,default=None)
	nm_status = Field(String,default=None)
	fs_status = Field(String,default=None)
	iptables_status = Field(String,default=None)
	dns_status = Field(String,default=None)
	external_dns_status = Field(Boolean,default=True)
	uptime = Field(String,default=None)	
	rpms = Field(String,default=None)	
	princeton_comon_dir = Field(Boolean,default=False)
	princeton_comon_running = Field(Boolean,default=False)
	princeton_comon_procs = Field(Int,default=None)

# EXTERNAL
	plc_node_stats = Field(PickleType,default=None)
	plc_site_stats = Field(PickleType,default=None)
	plc_pcuid      = Field(Int,default=None)
	comon_stats    = Field(PickleType,default=None)
	port_status    = Field(PickleType,default=None)
	firewall 		= Field(Boolean,default=False)
	ssh_portused = Field(Int,default=22)
	ssh_status = Field(Boolean,default=False)
	ssh_error = Field(String,default=None)	# set if ssh_access == False
	traceroute = Field(String,default=None)	
	ping_status = Field(Boolean,default=False)

# INFERRED
	observed_category = Field(String,default=None)
	observed_status = Field(String,default=None)

	acts_as_versioned(ignore=['date_checked'])
	# NOTE: this is the child relation
	#action = ManyToOne('ActionRecord', required=False)

class FindbadPCURecord(Entity):
	@classmethod
	def get_all_latest(cls):
		return cls.query.all()

	@classmethod
	def get_latest_by(cls, **kwargs):
		return cls.query.filter_by(**kwargs).first()

	def pcu_name(self):
		if self.plc_pcu_stats['hostname'] is not None and self.plc_pcu_stats['hostname'] is not "":
			return self.plc_pcu_stats['hostname']
		elif self.plc_pcu_stats['ip'] is not None and self.plc_pcu_stats['ip'] is not "":
			return self.plc_pcu_stats['ip']
		else:
			return None

	def format_ports(self):
		retval = []
		filtered_length=0

		supported_ports=reboot.model_to_object(self.plc_pcu_stats['model']).supported_ports
		data = self.port_status.copy()

		if data and len(data.keys()) > 0 :
			for port in supported_ports:
				try:
					state = data[str(port)]
				except:
					state = "unknown"

				if state == "filtered":
					filtered_length += 1
					
				retval.append( (port, state) )

		if retval == []: 
			retval = [( "Closed/Filtered", "" )]

		if filtered_length == len(supported_ports):
			retval = [( "All Filtered", "" )]

		return retval

	def format_pcu_shortstatus(self):
		status = "error"
		if self.reboot_trial_status:
			if self.reboot_trial_status == str(0):
				status = "Ok"
			elif self.reboot_trial_status == "NetDown" or self.reboot_trial_status == "Not_Run":
				status = self.reboot_trial_status
			else:
				status = "error"

		return status

	def test_is_ok(self):
		if self.reboot_trial_status == str(0):
			return True
		else:
			return False

	def pcu_errors(self):
		message = "\n"
		message += "\tModel: %s\n" % self.plc_pcu_stats['model']
		message += "\tMissing Fields: %s\n" % ( self.entry_complete == "" and "None missing" or self.entry_complete )
		message += "\tDNS Status: %s\n" % self.dns_status
		message += "\tPort Status: %s\n" % self.format_ports()
		message += "\tTest Results: %s\n" % self.format_pcu_shortstatus()
		return message

# ACCOUNTING
	date_checked = Field(DateTime)
	round = Field(Int,default=0)
	plc_pcuid = Field(Int)

# EXTERNAL
	plc_pcu_stats = Field(PickleType,default=None)
	dns_status = Field(String)
	port_status = Field(PickleType)
	entry_complete = Field(String)

# INTERNAL
# INFERRED
	reboot_trial_status = Field(String)

	acts_as_versioned(ignore=['date_checked'])
