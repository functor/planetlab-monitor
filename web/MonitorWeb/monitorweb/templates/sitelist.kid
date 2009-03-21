<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor Site List"
from monitor.util import diff_time
from time import mktime
from links import *
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#"
	  xmlns:mochi="http://www.mochi.org">

  <div py:match="item.tag == 'content'">
  	<table width="100%">
		<thead>
			<tr>
				<th><a href="${link('site', filter='good')}">Compliant(${fc['good']})</a></th>
				<th><a href="${link('site', filter='down')}">Down(${fc['down']})</a></th>
				<th><a href="${link('site', filter='new')}">New Sites(${fc['new']})</a></th>
				<th><a href="${link('site', filter='pending')}">Disabled(${fc['pending']})</a></th>
				<th><a href="${link('site', filter='all')}">All(${fc['all']})</a></th>
			</tr>
		</thead>
		<tbody>
		<tr>
		<td colspan="5">
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th></th>
					<th>Site name</th>
					<th>Enabled</th>
					<th>Penalty</th>
					<th mochi:format="int">Slices/Max</th>
					<th mochi:format="int">Nodes/Total</th>
					<th>Last Change</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,site in enumerate(query)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					<td nowrap="true">
						<div class='oneline'>
						<a class='left' href="${link('pcuview', loginbase=site.loginbase)}">${site.loginbase}</a>
						<a class='right' href="${plc_site_uri(site.loginbase)}">
							<img style='display: inline' border='0' src="static/images/extlink.gif" align='right'/></a>
						</div>
					</td>
					<td py:content="site.enabled"></td>
					<td id="site-${site.penalty_level}">${site.penalty_level}</td>
					<td>${site.slices_used}/${site.slices_total}</td>
					<td>${site.nodes_up} / ${site.nodes_total}</td>
					<td id="site-${site.status}" py:content="diff_time(mktime(site.last_changed.timetuple()))"></td>
				</tr>
			</tbody>
		</table>
		</td>
		</tr>
		</tbody>
	</table>
  </div>

</html>
