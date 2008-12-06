<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor PCU View"
from monitor.util import diff_time
from monitor import config
from pcucontrol.reboot import pcu_name, model_to_object
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
    <h3>PCU Status</h3>
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th mochi:format="str">Site</th>
					<th>PCU Name</th>
					<th>Missing Fields</th>
					<th>DNS Status</th>
					<th>Port Status</th>
					<th width="80%">Test Results</th>
					<th>Model</th>
					<th>Nodes</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,node in enumerate(pcuquery)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td><a class="ext-link" href="${plc_site_link_id(node.plc_pcu_stats['site_id'])}">
							<span class="icon">${node.loginbase}</span>
						</a>
					</td>
					<td nowrap="true" >
						<a class="ext-link" href="${plc_pcu_link_id(node.plc_pcu_stats['pcu_id'])}">
							<span class="icon">${pcu_name(node.plc_pcu_stats)}</span>
						</a>
					</td>
					<td py:content="node.entry_complete"></td>
					<td id="dns-${node.dns_status}" py:content="node.dns_status"></td>
					<td>
						<span py:for="port,state in node.ports" 
						id="port${state}" py:content="'%s, ' % port">80</span>
					</td>
					<td width="40" id="status-${node.status}" py:content="node.reboot_trial_status"></td>
					<td py:content="node.plc_pcu_stats['model']"></td>
					<td py:content="len(node.plc_pcu_stats['node_ids'])"></td>
				</tr>
			</tbody>
		</table>
	<h3>Controls</h3>
		... node list ...
		<br/>
		form for reboot

	<h3>Legend</h3>

	<table border="1" align="center" width="80%">
		<tr><th colspan="2">Legend for 'DNS Status'</th></tr>

		<tr><td id="dns-DNS-OK">DNS-OK</td>
			<td>This indicates that the DNS name and registered IP address match.</td>
		</tr>
		<tr><td id="dns-DNS-MISMATCH">DNS-MISMATCH</td>
			<td>Sometimes, the registered IP and DNS IP address do not match.  
				In these cases it is not clear which is correct, 
				so an error is flagged.</td>
		</tr>
		<tr><td id="dns-DNS-NOENTRY">DNS-NOENTRY</td>
			<td>While a hostname is provided in the registration, the hostname is not actually registered in DNS.</td>
		</tr>
		<tr><td id="dns-NOHOSTNAME">NOHOSTNAME</td>
			<td>While we prefer that a hostname be registered, it is not
			strictly required, since simply the IP address, if it is static, is enough to access the PCU.</td>
		</tr>
		<tr><td>&nbsp;</td></tr>
	<!--/table>
	<table border=1-->
		<tr><th colspan="2">Legend for 'Port Status'</th></tr>

		<tr><td id="portopen">Open</td>
			<td>Green port numbers are believed to be open.</td>
		</tr>
		<tr><td id="portfiltered">Filtered</td>
			<td>Gold port numbers are believed to be filtered or simply offline.</td>
		</tr>
		<tr><td id="portclosed">Closed</td>
			<td>Finally, red ports appear to be closed.</td>
		</tr>
		<tr><td>&nbsp;</td></tr>
	<!--/table>
	<table border=1-->
		<tr><th colspan="2">Legend for 'Test Results'</th></tr>

		<tr><td id="status-0">OK</td>
			<td>The PCU is accessible, and short of actually rebooting the node, everything appears to work.</td>
		</tr>
		<tr><td id="status-NetDown">NetDown</td>
			<td>The PCU is inaccessible from the PlanetLab address block 128.112.139.0/25, or it is simply offline.</td>
		</tr>
		<tr><td id="status-Not_Run">Not_Run</td>
			<td>Previous errors, such as DNS or an incomplete configuration prevented the actual test from begin performed.</td>
		</tr>
		<tr><td id="status-error">Other Errors</td>
			<td>Other errors are reported by the test that are more specific to the block encountered by the script.</td>
		</tr>
	</table>

  </div>

</html>
