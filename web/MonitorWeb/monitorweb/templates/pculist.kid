<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor PCU View"
from pcucontrol.reboot import pcu_name, model_to_object
from monitor import config

def plc_site_link(pcu):
	return "https://" + config.MONITOR_HOSTNAME + "/db/sites/index.php?id=" + str(pcu['site_id'])

def pcu_link(pcu):
	return "https://" + config.MONITOR_HOSTNAME + "/db/sites/pcu.php?id=" + str(pcu['pcu_id'])

?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#">

  <div py:match="item.tag == 'content'">
  	<table width="100%">
		<thead>
			<tr>
				<th><a href="${tg.url('pcu', filter='ok')}">Ok(${fc['ok']})</a></th>
				<th><a href="${tg.url('pcu', filter='Not_Run')}">Misconfigured(${fc['Not_Run']})</a></th>
				<th><a href="${tg.url('pcu', filter='NetDown')}">Offline(${fc['NetDown']})</a></th>
				<th><a href="${tg.url('pcu', filter='pending')}">Runtime Error(${fc['pending']})</a></th>
				<th><a href="${tg.url('pcu', filter='all')}">All</a></th>
			</tr>
		</thead>
		<tbody>
		<tr>
		<td colspan="5">
		<table border="1">
			<thead>
				<tr>
					<th>Site</th>
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
				<tr py:for="i,node in enumerate(query)" class="${i%2 and 'odd' or 'even'}" >
					<td><a href="${plc_site_link(node.plc_pcu_stats)}">sitename</a></td>
					<td nowrap="true" >
						<a href="${pcu_link(node.plc_pcu_stats)}">${pcu_name(node.plc_pcu_stats)}</a></td>
					<td py:content="node.entry_complete"></td>
					<td id="dns-${node.dns_status}" py:content="node.dns_status"></td>
					<td>
						<span py:for="port,state in node.ports" 
						id="port${state}" py:content="'%s, ' % port">80</span>
					</td>
					<td id="status-${node.status}" py:content="node.reboot_trial_status"></td>
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
