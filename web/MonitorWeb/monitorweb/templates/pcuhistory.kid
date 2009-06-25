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
  	<h3>PCU History for pcu_id : <a href="${plc_pcu_uri_id(pcu_id)}">${pcu_id}</a></h3>
  	<table width="100%">
		<tbody>
		<tr>
		<td>
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th>Last Check</th>
					<th>Last Change</th>
					<th>pcu_id</th>
					<th>Status</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,pcu in enumerate(query)" class="${i%2 and 'odd' or 'even'}" >
					<td py:content="pcu.last_checked"></td>
					<td py:content="diff_time(mktime(pcu.last_changed.timetuple()))"></td>
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
