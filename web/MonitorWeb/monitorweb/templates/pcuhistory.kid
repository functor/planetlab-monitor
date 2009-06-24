<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "MyOps PCU History"
from monitor.util import diff_time
from time import mktime
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
  	<h3>Node History : ${pcu_id}</h3>
  	<table width="100%">
		<tbody>
		<tr>
		<td>
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<!--th>Site</th>
					<th>pcu</th-->
					<th>date</th>
					<th>pcu_id</th>
					<th>last_contact</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,pcu in enumerate(query)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<!--td id="site-${node.site.status}">
						<a href="${link('pcuview', loginbase=node.loginbase)}">${node.loginbase}</a>
					</td>
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
					</td-->
					<!--td id="node-${node.observed_status}" nowrap="true">
						<a target="_top" href="${link('pcuview', hostname=node.hostname)}" py:content="node.hostname">your.host.org</a></td-->
					<!--td nowrap="true" py:content="node.kernel"></td-->
					<!--td py:content="node.date_checked"></td-->
					<td py:content="pcu.last_checked"></td>
					<td nowrap="true">
						<a target="_top" href="${link('pcuview', pcuid=pcu.plc_pcuid)}" py:content="pcu.plc_pcuid">your.host.org</a></td>
					<td id="pcu-${pcu.status}" py:content="pcu.status"></td>
				</tr>
			</tbody>
		</table>
		</td>
		</tr>
		</tbody>
	</table>
  </div>

</html>
