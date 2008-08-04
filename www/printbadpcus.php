<?php 

function plc_site_link($site_name) 
{ 
	return "https://www.planet-lab.org/db/sites/index.php?site_pattern=" .  $site_name;
}

function pcu_link($pcu) 
{ 
	return "https://www.planet-lab.org/db/sites/pcu.php?id=" . $pcu['pcu_id']; 
}

function pcu_site($pcu)
{
	if ( array_key_exists('plcsite', $pcu) ):
		return $pcu['plcsite']['login_base'];
	else: 
		return "none";
	endif;
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
	if ( is_array($pcu) && array_key_exists('portstatus', $pcu) && count(array_keys($pcu['portstatus'])) > 0 )
	{
		$portstat = $pcu['portstatus'];

		#foreach ( array('22', '23', '80', '443') $portstat as $port => $state)
		foreach ( array('22', '23', '80', '443', '9100',  '16992') as $port)
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
function reboot_to_str($reboot)
{
	$ret = $reboot;
	switch ($reboot)
	{
		case "0":
			$ret = "OK";
			break;
		default:
			break;
	}
	return $ret;
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

include 'database.php';
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



if ( $_GET['category'] ) 
{
	$category = $_GET['category'];
	if ( $category == "node_ids" )
	{
		$newfunc = create_function('$pcu', 'return count($pcu[\'' . $category . '\']);');
	} else if ( $category == "login_base" )
	{
		$newfunc = create_function('$pcu', 'return $pcu[\'plcsite\'][\'' . $category . '\'];');
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

if ( $_REQUEST['id'] )
{
	$id = $_REQUEST['id'];
} else{
	$id = "all";
}
#print print_r($_SERVER) . "<BR>";

//array_multisort($protocols, SORT_ASC, SORT_STRING, $pculist);
?>

<title>PLC PCU Info</title>
<html>
<body>

<?php if ( $id == "all" ): ?>
	Total PCUs : <?= $total ?>
	<table border=1>
			<tr>
				<th>Count</th>
				<th><?= get_category_link("pcu_id", "PCU ID") ?></th>
				<th><?= get_category_link("login_base", "Site") ?></th>
				<th><?= get_category_link("hostname", "PCU Name") ?></th>
				<th><?= get_category_link("complete_entry", "Incomplete Fields") ?></th>
				<th><?= get_category_link("dnsmatch", "DNS Status") ?></th>
				<th><?= get_category_link("portstatus", "Port Status") ?></th>
				<th><?= get_category_link("reboot", "Test Results") ?></th>
				<th><?= get_category_link("model", "Model") ?></th>
				<th><?= get_category_link("node_ids", "Nodes") ?></th>
			</tr>
	<?php $count = 0; ?>
	<?php $reachable_nodes = 0; ?>
	<?php foreach ( $pculist as $pcu ): ?>
			<tr>
				<td><?= $count ?></td>
				<td id='id<?= $pcu['pcu_id'] ?>'><a href='<?= pcu_link($pcu) ?>'><?= $pcu['pcu_id'] ?></a></td>
				<td><a href='<?= plc_site_link(pcu_site($pcu)) ?>'><?= pcu_site($pcu) ?></a></td>
				<td><?= pcu_name($pcu) ?></td>
				<td><?= pcu_entry($pcu) ?></td>
				<td bgcolor='<?= DNS_to_color($pcu['dnsmatch']) ?>'><?= $pcu['dnsmatch'] ?></td>
				<td><?= format_ports($pcu) ?></td>
				<td bgcolor='<?= reboot_to_color($pcu['reboot']) ?>'><?= reboot_to_str($pcu['reboot']) ?></td>
				<td nowrap><?= $pcu['model'] ?></td>
				<td><?= count( $pcu['node_ids'] ) ?></td>
			</tr>

	<?php if ( $pcu['reboot'] == "0" ) $reachable_nodes+=count($pcu['node_ids']); ?>
	<?php $count += 1; ?>
	<?php endforeach; ?>
	</table>
	<b>Reachable Nodes:</b> <?= $reachable_nodes ?>
<?php else: ?>
	<table align=center border=1>
			<tr>
				<th><?= get_category_link("pcu_id", "PCU ID") ?></th>
				<th><?= get_category_link("login_base", "Site") ?></th>
				<th><?= get_category_link("hostname", "PCU Name") ?></th>
				<th><?= get_category_link("complete_entry", "Incomplete Fields") ?></th>
				<th><?= get_category_link("dnsmatch", "DNS Status") ?></th>
				<th><?= get_category_link("portstatus", "Port Status") ?></th>
				<th><?= get_category_link("reboot", "Test Results") ?></th>
				<th><?= get_category_link("model", "Model") ?></th>
				<th><?= get_category_link("node_ids", "Nodes") ?></th>
			</tr>
	<?php $count = 0; ?>
	<?php $reachable_nodes = 0; ?>
	<?php foreach ( $pculist as $pcu ): ?>
		<?php if ( $pcu['pcu_id'] == $id ): ?>
			<tr>
				<td id='id<?= $pcu['pcu_id'] ?>'><a href='<?= pcu_link($pcu) ?>'><?= $pcu['pcu_id'] ?></a></td>
				<td><a href='<?= plc_site_link(pcu_site($pcu)) ?>'><?= pcu_site($pcu) ?></a></td>
				<td><?= pcu_name($pcu) ?></td>
				<td><?= pcu_entry($pcu) ?></td>
				<td bgcolor='<?= DNS_to_color($pcu['dnsmatch']) ?>'><?= $pcu['dnsmatch'] ?></td>
				<td><?= format_ports($pcu) ?></td>
				<td bgcolor='<?= reboot_to_color($pcu['reboot']) ?>'><?= reboot_to_str($pcu['reboot']) ?></td>
				<td nowrap><?= $pcu['model'] ?></td>
				<td><?= count( $pcu['node_ids'] ) ?></td>
			</tr>
		<?php endif; ?>
	<?php endforeach; ?>
	</table>
	<br>
	<table border=1 align=center>
		<tr><th colspan=2>Legend for 'DNS Status'</th></tr>

		<tr><td bgcolor=lightgreen>DNS-OK</td>
			<td>This indicates that the DNS name and registered IP address match.</td>
		</tr>
		<tr><td bgcolor=lightgrey>DNS-MISMATCH</td>
			<td>Sometimes, the registered IP and DNS IP address do not match.  In these cases it is not clear which is correct, 
				so an error is flagged.</td>
		</tr>
		<tr><td bgcolor=lightgrey>DNS-NOENTRY</td>
			<td>While a hostname is provided in the registration, the hostname is not actually registered in DNS.</td>
		</tr>
		<tr><td bgcolor=white>NOHOSTNAME</td>
			<td>While we prefer that a hostname be registered, it is not
			strictly required, since simply the IP address, if it is static, is enough to access the PCU.</td>
		</tr>
	<!--/table>
	<table border=1-->
		<tr><th colspan=2>Legend for 'Port Status'</th></tr>

		<tr><td bgcolor=lightgreen>Open</td>
			<td>Green port numbers are believed to be open.</td>
		</tr>
		<tr><td bgcolor=gold>Filtered</td>
			<td>Gold port numbers are believed to be filtered or simply offline.</td>
		</tr>
		<tr><td bgcolor=indianred>Closed</td>
			<td>Finally, red ports appear to be closed.</td>
		</tr>
	<!--/table>
	<table border=1-->
		<tr><th colspan=2>Legend for 'Test Results'</th></tr>

		<tr><td bgcolor=darkseagreen>OK</td>
			<td>The PCU is accessible, and short of actually rebooting the node, everything appears to work.</td>
		</tr>
		<tr><td bgcolor=lightgrey>NetDown</td>
			<td>The PCU is inaccessible from the PlanetLab address block 128.112.139.0/25, or it is simply offline.</td>
		</tr>
		<tr><td bgcolor=lightgrey>Not_Run</td>
			<td>Previous errors, such as DNS or an incomplete configuration prevented the actual test from begin performed.</td>
		</tr>
		<tr><td bgcolor=indianred>Other Errors</td>
			<td>Other errors are reported by the test that are more specific to the block encountered by the script.</td>
		</tr>
	</table>
<?php endif; ?>


</body>
</html>
