<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
from monitor.util import diff_time
from time import mktime
from links import *
?>
<span xmlns:py="http://purl.org/kid/ns#">
	<span py:if="header is not None">
      <th class="sortable plekit_table">ID</th>
      <th class="sortable plekit_table">Hostname</th>
      <th class="sortable plekit_table">Site</th>
      <th class="sortable plekit_table">Ping</th>
      <th class="sortable plekit_table">SSH</th>
      <th class="sortable plekit_table">Stat</th>
      <th class="sortable plekit_table">pcu</th>
      <th class="sortable plekit_table">kernel</th>
      <th class="sortable plekit_table">BootCD</th>
      <th class="sortable plekit_table">Boot Server</th>
      <th class="sortable plekit_table">Installation Date</th>
      <th class="sortable-sortLastContact plekit_table">Last_contact</th>
	</span>
	<span py:if="node is not None">
        <td py:content="node.node.plc_node_stats['node_id']">node_id</td>
		<td nowrap="true">
		  <a target="_top" href="${link('pcuview', hostname=node.node.hostname)}" py:content="node.node.hostname">your.host.org</a></td>
		<td>
		  <a href="${link('pcuview', loginbase=node.node.loginbase)}">${node.node.loginbase}</a>
		</td>
                <td py:content="node.node.ping_status">ping</td>
                <td py:content="node.node.ssh_status">ssh</td>
                <td py:content="node.node.plc_node_stats['boot_state']">boot</td>
		<td width="20%" nowrap='true' align='center' id="status-${node.pcu_short_status}">
		  <div id="links">
		    <a class="info" py:if="'error' in node.pcu_short_status" 
		       href="${link('pcuview', pcuid=node.pcu.pcu.plc_pcuid)}">
		      Error<span><pre>${node.pcu.pcu.reboot_trial_status}</pre></span></a>
		    <a py:if="'error' not in node.pcu_short_status and 'none' not in node.pcu_short_status" 
		       href="${link('pcuview', pcuid=node.pcu.pcu.plc_pcuid)}"
		       py:content="node.pcu_short_status">Reboot Status</a>
		    <span py:if="'none' in node.pcu_short_status" 
			  py:content="node.pcu_short_status">Reboot Status</span>
		  </div>
		</td>
		<td nowrap="true" py:content="node.kernel"></td>
		<td nowrap="true" py:content="node.node.bootcd_version"></td>
		<td nowrap="true" py:content="node.node.boot_server"></td>
		<td nowrap="true" py:content="node.node.install_date"></td>
		<td  id="node-${node.node.observed_status}" py:content="diff_time(node.node.plc_node_stats['last_contact'])"></td>
	</span>
</span>
