
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
);

@Scrips = (
    {  ScripCondition => 'On Create',
       ScripAction    => 'AutoReply To Requestors',
       Template       => 'AutoReply' },
    {  ScripCondition => 'On Correspond',
       ScripAction    => 'Notify Requestors, Ccs and AdminCcs',
       Template       => 'PlanetLab Correspond with CC in body', },
    {  ScripCondition => 'On Create',
       ScripAction    => 'Notify AdminCcs',
       Template       => 'PlanetLab Create with CC in body', },
);

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
    {
      Queue       => '0',
      Name        => 'PlanetLab Correspond with CC in body',
      Description => 'Message with the recipients in the header',          # loc
      Content     => 'RT-Attach-Message: yes

Email Recipients (see http://PLC_RT_HOSTNAME/support )
    Owner: {$Ticket->OwnerObj->Name}
    Requestor: {$Ticket->RequestorAddresses}
{ if ($acc=$Ticket->AdminCcAddresses) { "    Ticket Ccs: " . $acc } }

==================================================

{$Transaction->Content()}
'
    },
    {
      Queue       => '0',
      Name        => 'PlanetLab Create with CC in body',
      Description => 'Create with CC in body',                 # loc
      Content     => 'RT-Attach-Message: yes

Email Recipients (see http://PLC_RT_HOSTNAME/support )
    Owner: {$Ticket->OwnerObj->Name}
    Requestor: {$Ticket->RequestorAddresses}
{ if ($acc=$Ticket->AdminCcAddresses) { "    Ticket Ccs: " . $acc } }

==================================================

{$Transaction->CreatedAsString}: Request {$Ticket->id} was acted upon.
Transaction: {$Transaction->Description}

Subject: {$Transaction->Subject || $Ticket->Subject || "(No subject given)"}

{$Transaction->Content()}
'
    },
);

@Queues = (
	   { Name              => 'monitor',
         Description       => 'Queue for monitor',
         CorrespondAddress => 'monitor@PLC_RT_HOSTNAME',
         CommentAddress    => '', },

	   { Name              => 'security',
         Description       => 'Queue for security issues',
         CorrespondAddress => 'security@PLC_RT_HOSTNAME',
         CommentAddress    => '', },

	   { Name              => 'legal',
         Description       => 'Queue for legal issues',
         CorrespondAddress => 'legal@PLC_RT_HOSTNAME',
         CommentAddress    => '', },
)
