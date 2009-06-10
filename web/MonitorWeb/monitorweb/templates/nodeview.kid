<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor Node View"
from monitor.util import diff_time
from time import mktime
from pcucontrol.reboot import pcu_name, model_to_object
from links import *
?>
<html	py:layout="'sitemenu.kid'"
	xmlns:py="http://purl.org/kid/ns#"
	xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
    <h3>Node Status</h3>
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th mochi:format="str">Site</th>
					<th>Hostname</th>
					<th>ping</th>
					<!--th>ssh</th-->
					<th>kernel</th>
					<th>last_change</th>
					<th>last_contact</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,node in enumerate(nodequery)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td><a class="ext-link" href="${plc_site_uri_id(node.plc_node_stats['site_id'])}">
							<span class="icon">${node.loginbase}</span></a>
					</td>
					<td id="node-${node.observed_status}" nowrap="true" >
						<a class="ext-link" href="${plc_node_uri_id(node.plc_nodeid)}">
							<span class="icon">${node.hostname}</span></a>
					</td>
					<td py:content="node.ping_status"></td>
					<td nowrap="true" py:content="node.kernel"></td>
					<td py:content="diff_time(mktime(node.history.last_changed.timetuple()))"></td>
					<td py:content="diff_time(node.plc_node_stats['last_contact'])"></td>
				</tr>
			</tbody>
		</table>
    <h3 py:if="node.pcu is not None">Controlling PCU</h3>
		<table py:if="node.pcu is not None" id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th>PCU Name</th>
					<th>Model</th>
					<th width="80%">Test Results</th>
				</tr>
			</thead>
			<tbody>
				<?python pcu = node.pcu ?>
				<tr>
					<td></td>
					<td nowrap="true" >
						<a class="ext-link" href="${plc_pcu_uri_id(pcu.plc_pcu_stats['pcu_id'])}">
							<span class="icon">${pcu_name(pcu.plc_pcu_stats)}</span>
						</a>
					</td>
					<td py:content="pcu.plc_pcu_stats['model']"></td>
					<td width="20%" nowrap='true' align='center' id="status-${node.pcu_short_status}">
						<div id="links">
							<a class="info" py:if="'error' in node.pcu_short_status" 
								href="${link('pcuview', pcuid=node.plc_pcuid)}">
								Error<span><pre>${node.pcu.reboot_trial_status}</pre></span></a>
							<a py:if="'error' not in node.pcu_short_status and 'none' not in node.pcu_short_status" 
								href="${link('pcuview', pcuid=node.plc_pcuid)}"
								py:content="node.pcu_short_status">Reboot Status</a>
							<span py:if="'none' in node.pcu_short_status" 
								py:content="node.pcu_short_status">Reboot Status</span>
						</div>
					</td>
				</tr>
			</tbody>
		</table>
    <h3>Actions Taken</h3>
  </div>

</html>
