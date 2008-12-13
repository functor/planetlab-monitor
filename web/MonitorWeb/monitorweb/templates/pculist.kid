<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor PCU List"
from pcucontrol.reboot import pcu_name, model_to_object
from monitor import config
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
  	<table id="sub-table" width="100%">
		<thead>
			<tr>
				<th><a href="${link('pcu', filter='ok')}">Ok(${fc['ok']})</a></th>
				<th><a href="${link('pcu', filter='Not_Run')}">Misconfigured(${fc['Not_Run']})</a></th>
				<th><a href="${link('pcu', filter='NetDown')}">Offline(${fc['NetDown']})</a></th>
				<th><a href="${link('pcu', filter='pending')}">Runtime Error(${fc['pending']})</a></th>
				<th><a href="${link('pcu', filter='all')}">All</a></th>
			</tr>
		</thead>
		<tbody>
		<tr>
		<td colspan="5">
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th mochi:format="str">Site</th>
					<th>PCU Name</th>
					<th>Missing Fields</th>
					<th>DNS Status</th>
					<th nowrap='true' >Port Status</th>
					<th nowrap='true' width="80%">Test Results</th>
					<th>Model</th>
					<th>Nodes</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,node in enumerate(query)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td><a href="${link('siteview', loginbase=node.loginbase)}">${node.loginbase}</a></td>
					<td nowrap='true'>
						<div class='oneline'>
						<a class='left' href="${link('pcuview', pcuid=node.plc_pcuid)}">${pcu_name(node.plc_pcu_stats)}</a>
						<a class='right' href="${plc_pcu_uri_id(node.plc_pcu_stats['pcu_id'])}">
							<img style='display: inline' border='0' src="static/images/extlink.gif" align='right'/></a>
						</div>
					</td>
					<td py:content="node.entry_complete"></td>
					<td id="dns-${node.dns_status}" py:content="node.dns_status"></td>
					<td>
						<span py:for="port,state in node.ports" 
						id="port${state}" py:content="'%s, ' % port">80</span>
					</td>
					<td width="20%" nowrap='true' align='center' id="status-${node.status}">
						<div id="links">
						<a class="info" py:if="'error' in node.status" 
							href="${link('pcuview', pcuid=node.plc_pcuid)}">
							Error Message<span><pre>${node.reboot_trial_status}</pre></span></a>
						<a py:if="'error' not in node.status" 
							href="${link('pcuview', pcuid=node.plc_pcuid)}"
							py:content="node.status">Reboot Status</a>
						</div>
					</td>
					<td py:content="node.plc_pcu_stats['model']"></td>
					<td py:content="len(node.plc_pcu_stats['node_ids'])"></td>
				</tr>
			</tbody>
		</table>
		</td>
		</tr>
		</tbody>
	</table>
  </div>

</html>
