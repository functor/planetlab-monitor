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
  <div py:if="len(sitequery) == 0">
  	<p>Your 'quick jump' query failed to find a matching site or hostname.</p>
	<p>MyOps recognizes three types of expressions:
	<ul>
	    <li>Site names, e.g. princeton, utah, nyu, etc</li>
	    <li>Host names, e.g. planetlab-1.cs.princeton.edu, pl1.university.edu, etc</li>
	    <li>Prefix a pattern with "site:" or "node:" to return all sites or
		nodes that match a pattern.  e.g. site:mlab* node:*redclara*</li>
	</ul>
	</p>
  </div>
  <div py:if="len(sitequery) != 0">
    <h3 py:if="len(sitequery) > 0">Site Status</h3>
		<table py:if="len(sitequery) > 0" id="sub-table" border="1" width="100%">
			<thead>
				<tr>
					<th>Status Since</th>
					<th>Site Name</th>
					<th>Enabled</th>
					<th>Penalty</th>
					<th>Slices/Max</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,site in enumerate(sitequery)" class="${i%2 and 'odd' or 'even'}" >
					<td id="site-${site.status}" py:content="diff_time(mktime(site.last_changed.timetuple()))"></td>
					<td id="site-${site.status}" nowrap="true"><a class="ext-link" href="${plc_site_uri_id(site.plc_siteid)}">
							<span class="icon">${site.loginbase}</span></a>
					</td>
					<td py:content="site.enabled"></td>
					<td id="site-${site.penalty_level}">${site.penalty_level}</td>
					<td>${site.slices_used}/${site.slices_total}</td>
					<td nowrap="true" width="70em"><a href="${link('detailview', loginbase=site.loginbase)}">More Details</a></td>
				</tr>
			</tbody>
		</table>
    <h3 py:if="len(pcuquery) != 0" >PCU Status</h3>
		<table py:if="len(pcuquery) != 0" id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th>Status Since</th>
					<th>PCU Name</th>
					<th>Model</th>
					<th>Nodes</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,agg in enumerate(pcuquery)" class="${i%2 and 'odd' or 'even'}" >
					<td id="site-${agg.pcuhist.status}" py:content="diff_time(mktime(agg.pcuhist.last_changed.timetuple()))"></td>
					<td nowrap="true" id="status-${agg.status}">
						<a class="ext-link" href="${plc_pcu_uri_id(agg.pcu.plc_pcu_stats['pcu_id'])}">
							<span class="icon">${pcu_name(agg.pcu.plc_pcu_stats)}</span>
						</a>
					</td>
					<td py:content="agg.pcu.plc_pcu_stats['model']"></td>
					<td py:content="len(agg.pcu.plc_pcu_stats['node_ids'])"></td>
					<td nowrap="true" width="70em"><a href="${link('detailview', pcuid=agg.pcu.plc_pcuid)}">More Details</a></td>
				</tr>
			</tbody>
		</table>
	<div class="oneline" id="legend" py:if="len(pcuquery) == 0">
		<h3>PCUs: None</h3>
	</div>
	<h3>Nodes</h3> 
		<p py:if="len(nodequery) == 0">
			There are no registered nodes for this site.
		</p>
		<table py:if="len(nodequery) > 0" id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th>Status Since</th>
					<th>Hostname</th>
					<th>last_checked</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,agg in enumerate(nodequery)" class="${i%2 and 'odd' or 'even'}" >
					<td id="site-${agg.history.status}" py:content="diff_time(mktime(agg.history.last_changed.timetuple()))"></td>
					<td id="node-${agg.node.observed_status}" nowrap="true" >
						<a class="ext-link" href="${plc_node_uri_id(agg.node.plc_node_stats['node_id'])}">
							<span class="icon">${agg.node.hostname}</span></a>
					</td>
					<td py:content="diff_time(mktime(agg.node.date_checked.timetuple()))"></td>
					<td nowrap="true" width="70em"><a href="${link('detailview', hostname=agg.node.hostname)}">More Details</a></td>
				</tr>
			</tbody>
		</table>
		<div class="error" py:if="exceptions is not None">
			${exceptions}
		</div>
		<div id="status_block" class="flash"
            py:if="value_of('tg_flash', None)" py:content="tg_flash"></div>

	${actionlist_widget.display(since=since, actions=actions)}
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
  </div>

</html>
