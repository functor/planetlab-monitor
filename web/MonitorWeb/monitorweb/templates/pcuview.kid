<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor PCU View"
from monitor.util import diff_time
from monitor import config
from time import mktime
from pcucontrol.reboot import pcu_name, model_to_object
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
    <h3 py:if="len(sitequery) > 0">Site Status</h3>
		<table py:if="len(sitequery) > 0" id="sub-table" border="1" width="100%">
			<thead>
				<tr>
					<th>Site name</th>
					<th>Enabled</th>
					<th>Penalty</th>
					<th>Slices/Max</th>
					<th>Nodes/Total</th>
					<th>Status</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,site in enumerate(sitequery)" class="${i%2 and 'odd' or 'even'}" >
					<td nowrap="true"><a class="ext-link" href="${plc_site_uri(site.loginbase)}">
							<span class="icon">${site.loginbase}</span></a>
					</td>
					<td py:content="site.enabled"></td>
					<td id="site-${site.penalty_level}">${site.penalty_level}</td>
					<td>${site.slices_used}/${site.slices_total}</td>
					<td>${site.nodes_up} / ${site.nodes_total}</td>
					<td id="site-${site.status}" py:content="diff_time(mktime(site.last_changed.timetuple()))"></td>
				</tr>
			</tbody>
		</table>
    <h3 py:if="len(pcuquery) != 0" >PCU Status</h3>
		<table py:if="len(pcuquery) != 0" id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th>PCU Name</th>
					<th>Missing Fields</th>
					<th>DNS Status</th>
					<th nowrap='true'>Port Status</th>
					<th width="80%">Test Results</th>
					<th>Model</th>
					<th>Nodes</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,pcu in enumerate(pcuquery)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td nowrap="true" >
						<a class="ext-link" href="${plc_pcu_uri_id(pcu.plc_pcu_stats['pcu_id'])}">
							<span class="icon">${pcu_name(pcu.plc_pcu_stats)}</span>
						</a>
					</td>
					<td py:content="pcu.entry_complete"></td>
					<td id="dns-${pcu.dns_status}" py:content="pcu.dns_status"></td>
					<td nowrap='true'>
						<span py:for="port,state in pcu.ports" 
						id="port${state}" py:content="'%s, ' % port">80</span>
					</td>
					<td width="40" id="status-${pcu.status}"><pre class="results" py:content="pcu.reboot_trial_status"></pre></td>
					<td py:content="pcu.plc_pcu_stats['model']"></td>
					<td py:content="len(pcu.plc_pcu_stats['node_ids'])"></td>
				</tr>
			</tbody>
		</table>
	<div class="oneline" id="legend" py:if="len(pcuquery) == 0">
		<em>There no PCUs associated with this host.</em>
	</div>
	<div class="oneline" id="legend" py:if="len(pcuquery) > 0">
		<em>Legend: </em>
		<a class="info" href="#">DNS Status<span>
			<table border="1" align="center" width="100%">
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
			</table>
			</span> </a> &nbsp;
		<a class="info" href="#">Port Status<span>
		<table border="1" align="center" width="100%">
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
		</table>
				</span> </a> &nbsp;
		<a class="info" href="#">Test Results<span>
		<table border="1" align="center" width="100%">
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
				</span> </a>
	</div>
	<h3>Nodes</h3>
		<p py:if="len(nodequery) == 0">
			There are no registered nodes for this site.
		</p>
		<table py:if="len(nodequery) > 0" id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th>Hostname</th>
					<th>last_contact</th>
					<th>last_checked</th>
					<th nowrap='true'>Port Status</th>
					<th></th>
					<th></th>
					<th></th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,node in enumerate(nodequery)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td id="node-${node.observed_status}" nowrap="true" >
						<a class="ext-link" href="${plc_node_uri(node.hostname)}">
							<span class="icon">${node.hostname}</span></a>
					</td>
					<td py:content="diff_time(node.plc_node_stats['last_contact'])"></td>
					<td py:content="diff_time(mktime(node.date_checked.timetuple()))"></td>
					<td>
						<span py:for="port,state in node.ports" 
						id="port${state}" py:content="'%s, ' % port">80</span>
					</td>
					<td>
						<!-- TODO: add some values/code to authenticate the operation.  -->
	  					<form action="${link('pcuview', hostname=node.hostname)}" name="externalscan${i}" method='post'>
						<input type='hidden' name='hostname' value='${node.hostname}'/> 
						<input type='hidden' name='type' value='ExternalScan' /> 
	  					</form>
						<a onclick='document.externalscan${i}.submit();' href="javascript: void(1);">ExternalScan</a>
					</td>
					<td>
						<!-- TODO: add some values/code to authenticate the operation.  -->
	  					<form action="${link('pcuview', hostname=node.hostname)}" name="internalscan${i}" method='post'>
						<input type='hidden' name='hostname' value='${node.hostname}'/> 
						<input type='hidden' name='type' value='InternalScan' /> 
	  					</form>
						<a onclick='javascript: document.internalscan${i}.submit();' href="javascript: void(1);">InternalScan</a>
					</td>
					<td py:if="len(pcuquery) > 0">
						<!-- TODO: add some values/code to authenticate the operation.  -->
	  					<form action="${link('pcuview', pcuid=pcu.plc_pcuid)}" name="reboot${i}" method='post'>
						<input type='hidden' name='hostname' value='${node.hostname}'/> 
						<input type='hidden' name='type' value='Reboot' /> 
	  					</form>
						<a onclick='javascript: document.reboot${i}.submit();' href="javascript: void(1);">Reboot</a>
					</td>
				</tr>
			</tbody>
		</table>
		<div class="error" py:if="exceptions is not None">
			${exceptions}
		</div>
		<div id="status_block" class="flash"
            py:if="value_of('tg_flash', None)" py:content="tg_flash"></div>

	<h4>Recent Actions</h4>
		<p py:if="actions and len(actions) == 0">
			There are no recent actions taken for this site.
		</p>
		<table py:if="actions and len(actions) > 0" id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th>Date</th>
					<th>Action taken on</th>
					<th>Action Type</th>
					<th>Message ID</th>
					<th>Errors</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,act in enumerate(actions)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td py:content="act.date_created"></td>
					<td py:if="act.hostname is not None" nowrap="true" >
						<a class="ext-link" href="${plc_node_uri(act.hostname)}">
							<span class="icon">${act.hostname}</span></a>
					</td>
					<td py:if="act.hostname is None" nowrap="true">
						<a class="ext-link" href="${plc_site_uri(act.loginbase)}">
							<span class="icon">${act.loginbase}</span></a>
					</td>
					<!--td py : content="diff_time(mktime(node.date_checked.timetuple()))"></td-->
					<td py:content="act.action_type"></td>
					<td py:content="act.message_id"></td>
					<td py:content="act.error_string"></td>
				</tr>
			</tbody>
		</table>

	<!-- TODO: figure out how to make this conditional by model rather than port;
				it is convenient to have links to ilo, drac, amt, etc.
				regardless of whether the last PCU scan was successful.  -->
	<h4 py:if="len(pcuquery) != 0">Convenience Calls</h4>
		<div py:if="len(pcuquery) != 0" class="code"> <!-- pcu is not None" class="code"-->
			<span	py:for="port,state in pcu.ports">
					<span class="code" py:if="port == 22 and state == 'open'">
						ssh -o PasswordAuthentication=yes -o PubkeyAuthentication=no 
						${pcu.plc_pcu_stats['username']}@${pcu_name(pcu.plc_pcu_stats)}
						<br/>
					</span>
					<span class="code" py:if="port == 23 and state == 'open'">
						telnet ${pcu_name(pcu.plc_pcu_stats)}
						<br/>
					</span>
					<span class="code" py:if="port == 80 and state == 'open'">
						<a href="http://${pcu_name(pcu.plc_pcu_stats)}">http://${pcu_name(pcu.plc_pcu_stats)}</a>
						<br/>
					</span>
					<span class="code" py:if="port == 443 and state == 'open'">
						<br/>
						<a href="https://${pcu_name(pcu.plc_pcu_stats)}">https://${pcu_name(pcu.plc_pcu_stats)}</a>
						<br/>
						curl -s --form 'user=${pcu.plc_pcu_stats['username']}' 
								--form 'password=${pcu.plc_pcu_stats['password']}' 
								--insecure https://${pcu_name(pcu.plc_pcu_stats)}/cgi-bin/webcgi/index
						<br/>
						/usr/share/monitor/pcucontrol/models/racadm.py -r ${pcu.plc_pcu_stats['ip']} 
							-u ${pcu.plc_pcu_stats['username']} -p '${pcu.plc_pcu_stats['password']}'
						<br/>
						/usr/share/monitor/pcucontrol/models/hpilo/locfg.pl 
							-f /usr/share/monitor/pcucontrol/models/hpilo/iloxml/Reset_Server.xml 
							-s ${pcu_name(pcu.plc_pcu_stats)}
							-u ${pcu.plc_pcu_stats['username']} 
							-p '${pcu.plc_pcu_stats['password']} ' | grep MESSAGE" 
					</span>
					<span class="code" py:if="port == 16992 and state == 'open'">
						/usr/share/monitor/pcucontrol/models/intelamt/remoteControl -A 
							-verbose 'http://${pcu_name(pcu.plc_pcu_stats)}:16992/RemoteControlService' 
							-user admin -pass '${pcu.plc_pcu_stats['password']}'
					</span>
			</span>
		</div>

  </div>

</html>
