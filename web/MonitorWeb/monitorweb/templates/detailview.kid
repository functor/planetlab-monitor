<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "MyOps Detail View"
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
					<th>History</th>
					<th>Status Since</th>
					<th>Site Name</th>
					<th>Enabled</th>
					<th>Penalty</th>
					<th>Slices/Max</th>
					<th>Nodes/Total</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,site in enumerate(sitequery)" class="${i%2 and 'odd' or 'even'}" >
					<td><a href="sitehistory?loginbase=${site.loginbase}">history</a></td>
					<td id="site-${site.status}" py:content="diff_time(mktime(site.last_changed.timetuple()))"></td>
					<td id="site-${site.status}" nowrap="true"><a class="ext-link" href="${plc_site_uri_id(site.plc_siteid)}">
							<span class="icon">${site.loginbase}</span></a>
					</td>
					<td py:content="site.enabled"></td>
					<td id="site-${site.penalty_level}">${site.penalty_level}</td>
					<td>${site.slices_used}/${site.slices_total}</td>
					<td>${site.nodes_up} / ${site.nodes_total}</td>
				</tr>
			</tbody>
		</table>
    <h3 py:if="len(pcuquery) != 0" >PCU Status</h3>
		<table py:if="len(pcuquery) != 0" id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th>History</th>
					<th>Status Since</th>
					<th>PCU Name</th>
					<th>Missing Fields</th>
					<th nowrap='true'>DNS Status</th>
					<th nowrap='true'>Port Status</th>
					<th width="80%">Test Results</th>
					<th>Model</th>
					<th>Nodes</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,agg in enumerate(pcuquery)" class="${i%2 and 'odd' or 'even'}" >
					<td><a href="pcuhistory?pcu_id=${agg.pcu.plc_pcuid}">history</a></td>
					<td nowrap="true" id="site-${agg.pcuhist.status}" py:content="diff_time(mktime(agg.pcuhist.last_changed.timetuple()))"></td>
					<td nowrap="true" id="status-${agg.status}">
						<a class="ext-link" href="${plc_pcu_uri_id(agg.pcu.plc_pcu_stats['pcu_id'])}">
							<span class="icon">${pcu_name(agg.pcu.plc_pcu_stats)}</span>
						</a>
					</td>
					<td py:content="agg.pcu.entry_complete"></td>
					<td nowrap='true' id="dns-${agg.pcu.dns_status}" py:content="agg.pcu.dns_status"></td>
					<td nowrap='true'>
						<span py:for="port,state in agg.ports" 
						id="port${state}" py:content="'%s, ' % port">80</span>
					</td>
					<td width="40" id="status-${agg.status}"><pre class="results" py:content="agg.pcu.reboot_trial_status"></pre></td>
					<td py:content="agg.pcu.plc_pcu_stats['model']"></td>
					<td py:content="len(agg.pcu.plc_pcu_stats['node_ids'])"></td>
				</tr>
			</tbody>
		</table>
	<div class="oneline" id="legend" py:if="len(pcuquery) == 0">
		<em>There are no PCUs associated with this host.</em>
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
					<th>History (scan)</th>
					<th>Status Since</th>
					<th>Hostname</th>
					<th>Resolves?</th>
					<th>SSH</th>
					<th>last_contact (cached)</th>
					<th>Last Checked</th>
					<th nowrap='true'>Port Status</th>
					<th>Blocked Ports?</th>
				</tr>
			</thead>
			<tbody>
				<span py:for="i,agg in enumerate(nodequery)">
				<tr class="${i%2 and 'odd' or 'even'}" >
					<td><a href="nodehistory?hostname=${agg.node.hostname}">status</a>
						(<a href="nodescanhistory?hostname=${agg.node.hostname}">scan</a>)</td>
					<td id="site-${agg.history.status}" py:content="diff_time(mktime(agg.history.last_changed.timetuple()))"></td>
					<td id="node-${agg.node.observed_status}" nowrap="true" >
						<a class="ext-link" href="${plc_node_uri_id(agg.node.plc_node_stats['node_id'])}">
							<span class="icon">${agg.node.hostname}</span></a>
					</td>
					<td py:content="agg.node.external_dns_status"></td>
					<td py:content="agg.node.ssh_status"></td>
					<td py:content="diff_time(agg.node.plc_node_stats['last_contact'])"></td>
					<td py:content="diff_time(mktime(agg.node.date_checked.timetuple()))"></td>
					<td>
						<span py:for="port,state in agg.ports" 
						id="port${state}" py:content="'%s, ' % port">80</span>
					</td>
					<td py:content="agg.node.firewall"></td>
				</tr>
				<tr>
					<td></td>
					<th>Kernel:</th>
					<td colspan="3" py:content="agg.kernel"> </td>
				</tr>
				<tr>
					<td></td>
					<th>DNS Status:</th>
					<td colspan="3"><pre py:content="agg.node.dns_status"> </pre></td>
				</tr>
				<tr>
					<td></td>
					<th>Traceroute:</th>
					<td colspan="3"><pre py:content="agg.node.traceroute"> </pre></td>
				</tr>
				</span>
			</tbody>
		</table>
		<div class="error" py:if="exceptions is not None">
			${exceptions}
		</div>
		<div id="status_block" class="flash"
            py:if="value_of('tg_flash', None)" py:content="tg_flash"></div>

	<h4>Actions Over the Last ${since} Days</h4>
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
					<td>
						<span py:if="act.message_id != 0">
							<a class="ext-link" href="${plc_mail_uri(act.message_id)}"><span class="icon">${act.message_id}</span></a>
						</span>
						<span py:if="act.message_id == 0">
							<a py:if="'bootmanager' in act.action_type or 'unknown' in act.action_type" href="/monitorlog/bm.${act.hostname}.log">latest bm log</a>
						</span>
					</td>
					<td><pre py:content="act.error_string"></pre></td>
				</tr>
			</tbody>
		</table>

	<!-- TODO: figure out how to make this conditional by model rather than port;
				it is convenient to have links to ilo, drac, amt, etc.
				regardless of whether the last PCU scan was successful.  -->
	<!--h4 py:if="len(pcuquery) != 0">Convenience Calls</h4>
		<div py:if="len(pcuquery) != 0" class="code"> 
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
						curl -s -form 'user=${pcu.plc_pcu_stats['username']}' 
								-form 'password=${pcu.plc_pcu_stats['password']}' 
								-insecure https://${pcu_name(pcu.plc_pcu_stats)}/cgi-bin/webcgi/index
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
		</div-->

  </div>

</html>
