<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "MyOps Detail View"
from monitor.util import diff_time
from monitor import config
from time import mktime
from pcucontrol.reboot import pcu_name, model_to_object
from links import *
?>
<html xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">
  <head>
    <link href="http://monitor.planet-lab.org/monitor/static/css/style.css" type="text/css" rel="stylesheet" />
  </head>

	<h3>Nodes for site ${loginbase}</h3> 
		<p>Working on the color...</p>
		<p py:if="len(nodequery) == 0">
			There are no registered nodes for this site.
		</p>
		<table py:if="len(nodequery) > 0" id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th>History</th>
					<th>Hostname</th>
					<th>Status</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,agg in enumerate(nodequery)" class="${i%2 and 'odd' or 'even'}" >
					<td><a target="_blank" href="nodehistory?hostname=${agg.node.hostname}">history</a></td>
					<td id="node-${agg.node.observed_status}" nowrap="true" >
						<a class="ext-link" target="_blank" href="${plc_node_uri_id(agg.node.plc_node_stats['node_id'])}">
							<span class="icon">${agg.node.hostname}</span></a>
					</td>
					<td py:content="agg.node.observed_status" nowrap="true" ></td>
				</tr>
			</tbody>
		</table>

</html>
