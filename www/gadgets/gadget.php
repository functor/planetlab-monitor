<?php
#function get_comon_count()
#{
#	$url = "http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeview&format=nameonly";
#	$count = `wget --quiet -O - "$url" | wc -l`;
#	return $count;
#}
#function get_comon_count_for($query)
#{
#	$url = "http://summer.cs.princeton.edu/status/tabulator.cgi?table=table_nodeviewshort&format=nameonly&select='$query'";
#	$count = `wget --quiet -O - "$url" | wc -l`;
#	return $count;
#}
#$total = get_comon_count();
#$alive = get_comon_count_for("lastcotop==0");
#$fc2 = get_comon_count_for("fcname==2");
#$fc4 = get_comon_count_for("fcname==4");
#$not_alive = $total - $alive;
#$nossh = get_comon_count_for("sshstatus>0||sshstatus<0");
#$unknown = abs($not_alive - $nossh);
#$time = date("D M j G:i:s");
#$monday_csv_list= trim(file_get_contents("monday.txt"));
#$monday_array = split(",", $monday_csv_list);

$bad_csv_list= trim(file_get_contents("badcsv.txt"));
$sarray = split(",", $bad_csv_list);	# split on comma

$alpha_running = $sarray[0];
$prod_running = $sarray[1];
$oldboot_running = $sarray[2];
$alpha_debug = $sarray[3];

$prod_debug = $sarray[4];
$oldboot_debug = $sarray[5];
$down = $sarray[6];
#$prod_since_monday = $alpha_running - $monday_array[0];
#$oldboot_since_monday = $monday_array[1] - $oldboot_running;
$monitor_total = $prod_running + $prod_debug + $down +$oldboot_running + $oldboot_debug + $alpha_running + $alpha_debug;
?>

<table cellspacing=3>
<!--/table>

<table cellspacing=3-->
<tr>
<th align=left>MONITOR</th>
<th align=right>Boot</th>
<th align=right>Debug</th>
<th align=right>Down</th>
<th align=right></th>
</tr> 
<tr> 
<th align=left>Production 4.2</th> 
<td bgcolor=lightgrey align=right><?php echo $alpha_running ?></td> 
<td align=right><?php echo $alpha_debug + $prod_debug ?></td> 
<td align=right><?php echo $down ?></td>
<td align=right><?php echo ($alpha_running + $alpha_debug + $prod_debug + $down) ?></td> 
</tr> 
<tr> 
<th align=left>Production 4.1</th> 
<td align=right><?php echo $prod_running ?></td> 
<td align=right>--</td> 
<td align=right>--</td> 
<td align=right><?php echo ($prod_running) ?></td>
</tr> 
<tr> 
<th align=left>Old BootCD</th> 
<td align=right><?php echo $oldboot_running ?></td> 
<td align=right><?php echo $oldboot_debug ?></td> 
<td align=right>--</td> 
<td align=right><?php echo ($oldboot_running + $oldboot_debug) ?></td> 
<tr> 
<th align=left>Sums</th> 
<td align=right><?php echo $prod_running+$alpha_running+$oldboot_running ?></td> 
<td align=right><?php echo $prod_debug+$oldboot_debug+$alpha_debug ?></td> 
<td align=right>--</td>
<td bgcolor=lightgrey align=right><?php echo ($prod_running + $prod_debug + $down +$oldboot_running + $oldboot_debug + $alpha_running + $alpha_debug) ?></td>
</tr> 
<tr> 
<th align=left></th> 
<td align=right><?php echo sprintf("%.1f%%", ($prod_running+$alpha_running+$oldboot_running)/1.0/$monitor_total*100) ?></td> 
<td align=right><?php echo sprintf("%.1f%%", (($prod_debug+$oldboot_debug+$alpha_debug)/1.0/$monitor_total*100)) ?></td>
<td align=right><?php echo sprintf("%.1f%%", ($down/1.0/$monitor_total*100)) ?></td>
<td align=right></td>
</tr> 
<tr> 
<td>
<a target=_blank href="http://monitor.planet-lab.org/monitor/gadget.php">Direct Link</a>
</td>
</tr> 
</table>
