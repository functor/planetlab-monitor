<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "MyOps Node History"
from monitor.util import diff_time
from time import mktime
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
  	<h3>Node History : ${hostname}</h3>
  	<table width="100%">
		<tbody>
		<tr>
		<td>
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th>Last Check</th>
					<th>Last Change</th>
					<th>hostname</th>
					<th>Status</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,node in enumerate(query)" class="${i%2 and 'odd' or 'even'}" >
					<td py:content="node.last_checked"></td>
					<td py:content="diff_time(mktime(node.last_changed.timetuple()))"></td>
					<td nowrap="true">
						<a target="_top" href="${link('pcuview', hostname=node.hostname)}" py:content="node.hostname">your.host.org</a></td>
					<td id="node-${node.status}" py:content="node.status"></td>
				</tr>
			</tbody>
		</table>
		</td>
		</tr>
		</tbody>
	</table>
  </div>

</html>
