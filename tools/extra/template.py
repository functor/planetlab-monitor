#!/usr/bin/python


from monitor.wrapper import emailTxt
class Type:
	def __init__(self, value):
		self.value = value
	def name(self):
		return self.__class__.__name__
	
class Is(Type): pass
class Match(Type): pass
class ListMatch(Type): pass
class FilledIn(Type): pass
class PortOpen(Type): pass
class NodesUp(Type): pass

# a failed constraint leads to a message-escelation process.
# so, define a constraint, which defines the set of nodes it operates on, the
# 	  message to send if it fails, and maybe a thank you message when it's
# 	  satisfied (if previously failed.).
standardnode = {
	'membership' : [ { 'plcnode/nodegroups' : Match('.*') } ],
	'site'       : [ { 'nodes'    : NodesUp(2), } ],
	'node'       : { 'constraint' : 
								[ {	'state'    : Match('BOOT'),
								'kernel'   : Match('2.6.22.19-vs2.3.0.34'), } ],
					 'failed_message'	: [ emailTxt.mailtxt.newdown ],
					 'resolved_message'	: [ emailTxt.mailtxt.newthankyou ],
					},
	'pcu'		 : { 
					 'constraint' : [ {	'hostname' : FilledIn(True),
										'password' : FilledIn(True), },
									 {	'ip' : FilledIn(True),
										'password' : FilledIn(True), },
									],
					 'failed_message'	: [ emailTxt.mailtxt.pcudown ],
					 'resolved_message'	: [ emailTxt.mailtxt.pcuthankyou ],
					},
}

dc7800 = {
	# if membership constraint it true, then apply the other constraints.
	'membership'	: [ { 'plcnode/nodegroups' : ListMatch('DC7800Deployment'), } ],

	'pcu'			: { 'constraint' : [ { 'hostname'	: FilledIn(True),
									'ip' 		: FilledIn(True),
									'password'	: FilledIn(True),
									'model'		: Match('AMT'),
									'username'	: Match('admin'),
									'portstatus': PortOpen(16992),
									'reboot' 	: Is(0),
								 },
								 {	'hostname'	: FilledIn(True),
									'ip' 		: FilledIn(True),
									'password'	: FilledIn(True),
									'reboot'	: Is(0),
									#'valid'		: Is(True),
								 },],
					 'failed_message'	: [ emailTxt.mailtxt.donation_nopcu],
					 'resolved_message'	: [ emailTxt.mailtxt.pcuthankyou ],
					 },
	'node'       : { 'constraint' : 
								[ {	'state'    : Match('BOOT'),
									'kernel'   : Match('2.6.22.19-vs2.3.0.34'), } ],
					 'failed_message'	: [ emailTxt.mailtxt.donation_down],
					 'resolved_message'	: [ emailTxt.mailtxt.newthankyou ],
				},
}

#
# data source, { constraints ... value } 
# action on failure of constraint
# information about why it failed
# # stop action if constraint is satisfied at a later time.
# kind of like asynchronous constraint solving.
# or stored procedures.
