<?php 


function pcu_link($pcu) 
{ 
	return "https://www.planet-lab.org/db/sites/pcu.php?id=" . $pcu['pcu_id']; 
}

function pcu_name($pcu)
{
	if ( $pcu['hostname'] != NULL and $pcu['hostname'] != "" ):
		return $pcu['hostname'];
	else: 
		return $pcu['ip'];
	endif;
}
function pcu_entry($pcu)
{
	if ( count($pcu['complete_entry']) > 0 ) {
		return join("<BR>", $pcu['complete_entry']);
	} else {
		return "&nbsp;";
	}
}

function format_ports($pcu)
{
	$str = "";
	#print print_r(is_array($pcu)) . "<BR>";
	#print print_r(array_key_exists('portstatus', $pcu)) . "<BR>";
	if ( is_array($pcu) && array_key_exists('portstatus', $pcu) )
	{
		$portstat = $pcu['portstatus'];

		#foreach ( array('22', '23', '80', '443') $portstat as $port => $state)
		foreach ( array('22', '23', '80', '443') as $port)
		{
			$state = $portstat[$port];
			switch ($state)
			{
				case "open":
					$color = "lightgreen";
					break;
				case "filtered":
					$color = "gold";
					break;
				case "closed":
					$color = "indianred";
					break;
				default:
					$color = "white";
					break;
			}
			$str .= "<span style='background-color: $color'>$port</span>&nbsp;"; 
			#  . ":&nbsp;" . $state . "<br>";
		}
	} else {
	#	print print_r(is_array($pcu)) . "<BR>";
	#	print print_r(array_key_exists('portstatus', $pcu)) . "<BR>";
		#echo "<pre>";
		#print_r($pcu['portstatus']);
		#echo "</pre>";
	}
	if ( $str == "" )
	{
		$str = "Closed/Filtered";
	}
	return $str;
}
function DNS_to_color($dns)
{
	switch ($dns)
	{
		case "DNS-OK":
			return 'lightgreen';
		case "NOHOSTNAME":
			return 'white';
		case "DNS-MISMATCH":
			return 'gold';
		case "NO-DNS-OR-IP":
		case "DNS-NOENTRY":
			return 'indianred';
	}
	return 'white';
}

function reboot_to_color($reboot)
{
	switch ($reboot)
	{
		case "0":
			return "darkseagreen";
			break;
		case "NetDown":
			return "lightgrey";
			break;
		case "Not_Run":
			return "lightgrey";
			break;
		case "Unsupported_PCU":
			return "indianred";
			break;
		default:
			if ( strpos($reboot, "error") >= 0)
			{
				return "indianred";
			} else {
				return 'white';
			}
			break;
	}
	return "white";
}

function get_pcuid($pcu) { return $pcu['pcu_id']; }
function get_dns($pcu) { return $pcu['dnsmatch']; }
function get_dryrun($pcu) { return $pcu['reboot']; }
function get_model($pcu) { return $pcu['model']; }
function get_category_link($category,$header) 
{ 
	return "<a href='printbadpcus.php?category=$category'>$header</a>"; 
}

include 'soltesz.php';
$p = new Pickle();
$findbad = $p->load("findbadpcus");
$findbadpcus = array_keys($findbad['nodes']);

$pculist = array();
$c = 0;
foreach ( $findbadpcus as $pcu_id )
{
	if ( is_array($findbad['nodes'][$pcu_id]) ) 
	{
		#if ( in_array('values', $findbad['nodes'][$pcu]) )
		#{
		#	echo $pcu . " true<BR>";
		#} else{
		#	echo $pcu . " false<br>";
		#}
		if ( array_key_exists('values', $findbad['nodes'][$pcu_id]) )
		{
			$pculist[] = $findbad['nodes'][$pcu_id]['values'];
		}
	}
}
$total = count($pculist);


## Sort the pculist

#$pcu_ids = array_map('get_pcuid', $pculist);
#array_multisort($pcu_ids, SORT_ASC, SORT_NUMERIC, $pculist);

#$dns_ids = array_map('get_dns', $pculist);
#array_multisort($dns_ids, SORT_ASC, SORT_STRING, $pculist);

#$dry_ids = array_map('get_dryrun', $pculist);
#array_multisort($dry_ids, SORT_ASC, SORT_STRING, $pculist);
if ( $_GET['category'] ) 
{
	$category = $_GET['category'];
	if ( $category == "node_ids" )
	{
		$newfunc = create_function('$pcu', 'return count($pcu[\'' . $category . '\']);');
	} else {
		$newfunc = create_function('$pcu', 'return $pcu[\'' . $category . '\'];');
	}
	if ( $newfunc != "" )
	{
		$fields = array_map($newfunc, $pculist);
		array_multisort($fields, SORT_ASC, SORT_STRING, $pculist);
	} else {
		echo "ERROR create_function == null<BR>";
	}
}

if ( $_GET['auth'] )
{
	$auth = True;
} else {
	$auth = False;
}


//array_multisort($protocols, SORT_ASC, SORT_STRING, $pculist);
?>

<title>PLC PCU Info</title>
<html>
<body>

Total PCUs : <?= $total ?>
<table border=1>
		<tr>
			<th>Count</th>
			<th><?= get_category_link("pcu_id", "PCU ID") ?></th>
			<th><?= get_category_link("hostname", "Hostname") ?></th>
			<th><?= get_category_link("complete_entry", "Incomplete Fields") ?></th>
			<th><?= get_category_link("dnsmatch", "DNS Status") ?></th>
			<th><?= get_category_link("portstatus", "Port Status") ?></th>
			<th><?= get_category_link("reboot", "Dry Run Results") ?></th>
			<th><?= get_category_link("model", "Model") ?></th>
			<th><?= get_category_link("node_ids", "Nodes") ?></th>
			<?php if ( $auth ): ?>
				<th>Username</th>
				<th>Password</th>
				<th>Notes</th>
			<?php endif; ?>
		</tr>
<?php $count = 0; ?>
<?php foreach ( $pculist as $pcu ): ?>
		<tr>
			<td><?= $count ?></td>
			<td id='id<?= $pcu['pcu_id'] ?>'><a href='<?= pcu_link($pcu) ?>'><?= $pcu['pcu_id'] ?></a></td>
			<td><?= pcu_name($pcu) ?></td>
			<td><?= pcu_entry($pcu) ?></td>
			<td bgcolor='<?= DNS_to_color($pcu['dnsmatch']) ?>'><?= $pcu['dnsmatch'] ?></td>
			<td><?= format_ports($pcu) ?></td>
			<td bgcolor='<?= reboot_to_color($pcu['reboot']) ?>'><?= $pcu['reboot'] ?></td>
			<td nowrap><?= $pcu['model'] ?></td>
			<td><?= count( $pcu['node_ids'] ) ?></td>
			<?php if ( $auth ): ?>
				<td><?= ( $pcu['username'] ? $pcu['username'] : "&nbsp;" ) ?></td>
				<td><?= $pcu['password'] ?></td>
				<td><?= $pcu['notes'] ?></td>
			<?php endif; ?>
		</tr>
<?php $count += 1; ?>
<?php endforeach; ?>
</table>

</body>
</html>
