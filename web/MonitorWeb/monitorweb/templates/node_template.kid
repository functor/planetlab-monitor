<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
from monitor.util import diff_time
from time import mktime
from links import *
?>
<span xmlns:py="http://purl.org/kid/ns#">
	<span py:if="header is not None">
		<th>Site</th>
                <th>Ping</th>
                <th>SSH</th>
                <th>Boot Status</th>
		<th>pcu</th>
		<th>Hostname</th>
                <th>ID</th>
		<th>kernel</th>
		<th>last_contact</th>
	</span>
	<span py:if="node is not None">
		<td id="site-${node.site.status}">
			<a href="${link('pcuview', loginbase=node.loginbase)}">${node.loginbase}</a>
		</td>
                <td py:content="node.ping_status">ping</td>
                <td py:content="node.ssh_status">ssh</td>
                <td py:content="node.plc_node_stats['boot_state']">boot</td>
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
		<td id="node-${node.observed_status}" nowrap="true">
			<a target="_top" href="${link('pcuview', hostname=node.hostname)}" py:content="node.hostname">your.host.org</a></td>
                <td py:content="node.plc_node_stats['node_id']">node_id</td>
		<td nowrap="true" py:content="node.kernel"></td>
		<td py:content="diff_time(node.plc_node_stats['last_contact'])"></td>
	</span>
</span>
