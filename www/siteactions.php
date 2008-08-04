<?php 

function get_category_link($category,$header) 
{ 
	return "<a href='siteactions.php?category=$category'>$header</a>"; 
}
function rt_link ($ref, $id)
{
	$slink = sprintf("<a href='https://rt.planet-lab.org/Ticket/Display.html".
			"?user=guest&pass=guest&id=%s'>%s #%s</a>", $id, $ref, $id);
	return $slink;
}

function history_link($nodename)
{
	return sprintf("<a href='siteactions.php?history=%s'>%s</a>", $nodename, $nodename);
}

class Event
{
	function Event($event_record)
	{
		$this->data = $event_record;
	}
	public function getTime()
	{
		if ( array_key_exists('time', $this->data) )
		{
			$stime=strftime("%Y/%m/%d %H:%M", $this->data['time']);
			return $stime;
		} else {
			return "";
		}	
	}
	public function getField($field)
	{
		if ( array_key_exists($field, $this->data ) )
		{
			# truncate the stage_ part.
			#event['stage'] = event['stage'][6:]
			if ( is_array($this->data[$field]) and $field != "info" ):
				$ret = $this->data[$field][0];
			elseif ( is_array($this->data[$field]) and $field == "info" ):
				$ar = $this->data[$field];
				$ret = sprintf("%s -> %s", $ar[1] , $ar[2]);
			else:
				$ret = $this->data[$field];
			endif;
		} else {
			$ret = "&nbsp;";
		}
		return $ret;

	}
	public function getRTTicket()
	{
		if ( array_key_exists('ticket_id', $this->data) and 
		     $this->data['ticket_id'] != "" )
		{
			$rt_ticket = $this->data['ticket_id'];
			$slink = rt_link("Monitor", $rt_ticket);

		} elseif ( array_key_exists('found_rt_ticket', $this->data) and 
		     		$this->data['found_rt_ticket'] != "" ) {
			$rt_ticket = $this->data['found_rt_ticket'];
			$slink = rt_link("Support", $rt_ticket);
		} else {
			$slink = "No tickets";
		}
		return $slink;
	}
}

include 'database.php';
$p = new Pickle();
$act_all = $p->load("act_all");
$plcdb_hn2lb = $p->load("plcdb_hn2lb");
$findbad = $p->load("findbadnodes");
$findbadnodes = array_keys($findbad['nodes']);

$sickdb = array();

$all_hosts = array_keys($act_all);
foreach ( $all_hosts as $nodename):
	$diag_nodelist = $act_all[$nodename];
	if ( array_key_exists($nodename, $plcdb_hn2lb) )
		$lb = $plcdb_hn2lb[$nodename];
		if ( ! array_key_exists($lb, $sickdb) )
			$sickdb[$lb] = array();
		$sickdb[$lb][$nodename] = $diag_nodelist;
endforeach;

if ( array_key_exists('history', $_GET) )
{
	$history_nodename = $_GET['history'];
	$all_loginbases = array($plcdb_hn2lb[$history_nodename]);
	$get_history = TRUE;
} else {
	$all_loginbases = array_keys($sickdb);
	sort($all_loginbases);
	$get_history = FALSE;
}

$display = array();

foreach ( $all_loginbases as $loginbase ):
	$nodedict = $sickdb[$loginbase];
	$hosts = array_keys($nodedict);
	sort($hosts);
	if ( $get_history ) {
		$nodename = $history_nodename;
		foreach ( $act_all[$nodename] as $event_record ):
			
			$event = new Event($event_record);
			$row = array();
			$row['loginbase'] = $loginbase;
			$row['hostname'] = history_link($nodename);
			$row['time'] = $event->getTime();
			$row['ticket_id'] = $event->getRTTicket();
			foreach ( array('category', 'action', 'stage', 'info') as $field )
			{
				$row[$field] = $event->getField($field);
			}
			$display[] = $row;
		endforeach;
	} elseif ( ! $get_history ) {
		foreach ( $hosts as $nodename ):
			if ( count($act_all[$nodename]) == 0 ) continue;
			
			$event = new Event($act_all[$nodename][0]);
			$row = array();
			$row['loginbase'] = $loginbase;
			$row['hostname'] = history_link($nodename);
			#$row['time'] = "<pre>" . print_r($act_all[$nodename][0], TRUE) .  "</pre>";
			$row['time'] = $event->getTime();
			$row['ticket_id'] = $event->getRTTicket();
			$row['plcstate'] = $event->data['plcnode']['boot_state'];
			$row['currentcategory'] = $findbad['nodes'][$nodename]['values']['category'] . 
								"-" . $findbad['nodes'][$nodename]['values']['state'];
			foreach ( array('category', 'action', 'stage', 'info') as $field )
			{
				$row[$field] = $event->getField($field);
			}

			$display[] = $row;
		endforeach;
	}
endforeach;
?>

<title>siteactions.php</title>
<html>
<body>


<table width=80% border=1>
	<tr>
		<th>Count</th>
		<th><?= get_category_link("loginbase", "SiteID") ?></th>
		<th><?= get_category_link("hostname", "Hostname") ?></th>
		<?php if ( $get_history ): ?>
			<th><?= get_category_link("time", "Time") ?></th>
		<?php endif; ?>
		<th><?= get_category_link("ticket_id", "RT Ticket") ?></th>
		<th><?= get_category_link("category", "Last Category") ?></th>
		<?php if ( $get_history ): ?>
			<th><?= get_category_link("action", "Action") ?></th>
		<?php else: ?>
			<th><?= get_category_link("currentcategory", "Current Category") ?></th>
			<th><?= get_category_link("action", "Last Action") ?></th>
		<?php endif; ?>
		<th><?= get_category_link("stage", "Stage") ?></th>
		<th><?= get_category_link("info", "Info") ?></th>
	</tr>
<?php $count = 0; ?>
<?php foreach ( $display as $row ): ?>
	<tr>
		<td><?= $count ?></td>
		<td><?= $row['loginbase'] ?></td>
		<td><?= $row['hostname'] ?></td>
		<?php if ( $get_history ): ?>
			<td nowrap><?= $row['time'] ?></td>
		<?php endif; ?>
		<td nowrap><?= $row['ticket_id'] ?></td>
		<td><?= $row['category'] ?>/<?= $row['plcstate'] ?></td>
		<?php if ( ! $get_history ): ?>
			<td><?= $row['currentcategory'] ?></td>
		<?php endif; ?>
		<td><?= $row['action'] ?></td>
		<td><?= $row['stage'] ?></td>
		<td nowrap><?= $row['info'] ?></td>
	</tr>
<?php $count += 1; ?>
<?php endforeach; ?>
</table>

</body>
</html>
