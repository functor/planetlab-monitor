
@ACL = (
	{ GroupDomain => 'SystemInternal',
	  GroupType => 'Everyone',
	  Right => 'CreateTicket', },

	{ GroupDomain => 'SystemInternal',
	  GroupType => 'Everyone',
	  Right => 'ReplyToTicket', },

	{ GroupDomain => 'RT::System-Role',
	  GroupType => 'AdminCc',
	  Right => 'WatchAsAdminCc', },
	  
	{ GroupDomain => 'RT::System-Role',
	  GroupType => 'Cc',
	  Right => 'ReplyToTicket', },

	{ GroupDomain => 'RT::System-Role',
	  GroupType => 'Cc',
	  Right => 'Watch', },

	{ GroupDomain => 'RT::System-Role',
	  GroupType => 'Owner',
	  Right => 'ReplyToTicket', },

	{ GroupDomain => 'RT::System-Role',
	  GroupType => 'Owner',
	  Right => 'ModifyTicket', },
)
@Templates = (
    {  Queue       => '0',
       Name        => 'Autoreply',                                         # loc
       Description => 'Default Autoresponse template',                     # loc
       Content     => 'Subject: AutoReply: {$Ticket->Subject}

Hello,

Thank you very much for reporting this.

This message was automatically generated in response to the
creation of a trouble ticket regarding:

	"{$Ticket->Subject()}"

There is no need to reply to this message right now.  Your ticket has been
assigned an ID of [{$rtname} #{$Ticket->id()}].

Please include the string:

    [{$rtname} #{$Ticket->id}]

in the subject line of all future correspondence about this issue. To do so, 
you may reply to this message.

Thank you,
{$Ticket->QueueObj->CorrespondAddress()}

-------------------------------------------------------------------------
{$Transaction->Content()}
'
    },
)
