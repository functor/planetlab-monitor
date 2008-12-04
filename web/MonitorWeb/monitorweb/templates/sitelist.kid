<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor Site View"
?>
<html py:layout="'sitemenu.kid'"
      xmlns:py="http://purl.org/kid/ns#">

  <div py:match="item.tag == 'content'">
  	<table width="100%">
		<thead>
			<tr>
				<th><a href="${tg.url('site', filter='good')}">Compliant(${fc['good']})</a></th>
				<th><a href="${tg.url('site', filter='down')}">Down(${fc['down']})</a></th>
				<th><a href="${tg.url('site', filter='new')}">New Sites(${fc['new']})</a></th>
				<th><a href="${tg.url('site', filter='pending')}">Disabled(${fc['pending']})</a></th>
				<th><a href="${tg.url('site', filter='all')}">All(${fc['all']})</a></th>
			</tr>
		</thead>
		<tbody>
		<tr>
		<td colspan="5">
		<table id="sub-table" border="1" width="100%">
			<thead>
				<tr>
					<th>Site name</th>
					<th>Status</th>
					<th>Slices (created / max)</th>
					<th>Nodes (online / registered)</th>
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,site in enumerate(query)" class="${i%2 and 'odd' or 'even'}" >
				  <td nowrap="true"><a href="siteview?loginbase=${site.loginbase}">${site.loginbase}</a></td>
				  <td id="site-${site.status}" py:content="site.last_changed"></td>
				  <td>${site.slices_used}/${site.slices_total}</td>
				  <td>${site.nodes_up} / ${site.nodes_total}</td>
				</tr>
			</tbody>
		</table>
		</td>
		</tr>
		</tbody>
	</table>
  </div>

</html>
