<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor Site History List"
from monitor.util import diff_time
from time import mktime
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
  	<h3>Site History : ${loginbase}</h3>
  	<table width="100%">
		<tbody>
		<tr>
		<td>
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					<th>Site name</th>
					<th>Enabled</th>
					<th>Penalty</th>
					<th mochi:format="int">Slices/Max</th>
					<th mochi:format="int">Nodes/Total</th>
					<th>Date Checked</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,site in enumerate(query)">
					<td></td>
					<td nowrap="true">
						<div class='oneline'>
						<a class='left' href="${link('pcuview', loginbase=site.loginbase)}">${site.loginbase}</a>
						<a class='right' href="${plc_site_uri_id(site.plc_siteid)}">
							<img style='display: inline' border='0' src="static/images/extlink.gif" align='right'/></a>
						</div>
					</td>
					<td py:content="site.enabled"></td>
					<td id="site-${site.penalty_level}">${site.penalty_level}</td>
					<td>${site.slices_used}/${site.slices_total}</td>
					<td>${site.nodes_up} / ${site.nodes_total}</td>
					<td id="site-${site.status}" py:content="diff_time(mktime(site.last_changed.timetuple()))"></td>
					<td py:content="site.timestamp"></td>
				</tr>
			</tbody>
		</table>
		</td>
		</tr>
		</tbody>
	</table>
  </div>

</html>
