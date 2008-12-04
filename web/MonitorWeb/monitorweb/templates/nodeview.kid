<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor Site View"
from monitor.util import diff_time
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
					<th>pcu</th>
					<th>kernel</th>
					<th>last_contact</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,node in enumerate(nodequery)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td><a href="">${node.loginbase}</a></td>
					<td id="node-${node.observed_status}" nowrap="true" py:content="node.hostname"></td>
					<td py:content="node.ping_status"></td>
					<td id="status-${node.pcu_short_status}"><a href="pcuview?pcuid=${node.plc_node_stats['pcu_ids']}" py:content="node.pcu_short_status"></a></td>
					<td nowrap="true" py:content="node.kernel"></td>
					<td py:content="diff_time(node.plc_node_stats['last_contact'])"></td>
				</tr>
			</tbody>
		</table>
    <h3 py:if="node.pcu_short_status != 'none'">PCU Status</h3>
    <h3>Actions Taken</h3>
  </div>

</html>
