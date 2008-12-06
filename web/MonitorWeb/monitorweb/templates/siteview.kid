<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor Site View"
from monitor.util import diff_time
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
    <h3>Site Status</h3>
		<table id="sub-table" border="1" width="100%">
			<thead>
				<tr>
					<th>Site name</th>
					<th>Status</th>
					<th>Enabled</th>
					<th>Slices (created / max)</th>
					<th>Nodes (online / registered)</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,site in enumerate(sitequery)" class="${i%2 and 'odd' or 'even'}" >
					<td nowrap="true"><a class="ext-link" href="${plc_site_link(site.loginbase)}">
							<span class="icon">${site.loginbase}</span></a>
					</td>
				  <td id="site-${site.status}" py:content="site.last_changed"></td>
				  <td py:content="site.enabled"></td>
				  <td>${site.slices_used}/${site.slices_total}</td>
				  <td>${site.nodes_up} / ${site.nodes_total}</td>
				</tr>
			</tbody>
		</table>
    <h3>Node List</h3>
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th>Hostname</th>
					<th>ping</th>
					<!--th>ssh</th-->
					<th>pcu</th>
					<th>kernel</th>
					<th>last_contact</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,node in enumerate(nodequery)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td id="node-${node.observed_status}" nowrap="true"><a href="nodeview?hostname=${node.hostname}" py:content="node.hostname">your.host.org</a></td>
					<td py:content="node.ping_status"></td>
					<td py:if="node.pcu_short_status != 'none'" id="status-${node.pcu_short_status}">
						<a href="pcuview?pcuid=${node.plc_node_stats['pcu_ids']}">${node.pcu_short_status}</a></td>
					<td py:if="node.pcu_short_status == 'none'" id="status-${node.pcu_short_status}">
						${node.pcu_short_status}</td>
					<td nowrap="true" py:content="node.kernel"></td>
					<td py:content="diff_time(node.plc_node_stats['last_contact'])"></td>
				</tr>
			</tbody>
		</table>
  </div>

</html>
