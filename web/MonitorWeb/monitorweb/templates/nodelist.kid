<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<?python
layout_params['page_title'] = "Monitor Node List"
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
				<th><a href="${link('node', filter='BOOT')}">Production(${fc['BOOT']})</a></th>
				<th><a href="${link('node', filter='DEBUG')}">Debug(${fc['DEBUG']})</a></th>
				<th><a href="${link('node', filter='DOWN')}">Down(${fc['DOWN']})</a></th>
				<th><a href="${link('node', filter='neverboot')}">Never Booted(${fc['neverboot']})</a></th>
				<th><a href="${link('node', filter='pending')}">Pending Reply(${fc['pending']})</a></th>
				<th><a href="${link('node', filter='all')}">All</a></th>
			</tr>
		</thead>
		<tbody>
		<tr>
		<td colspan="5">
		<table id="sortable_table" class="datagrid" border="1" width="100%">
			<thead>
				<tr>
					<th mochi:format="int"></th>
					${nodewidget.display(node=None, header=True)}
				</tr>
			</thead>
			<tbody>
				<tr py:for="i,node in enumerate(query)" class="${i%2 and 'odd' or 'even'}" >
					<td></td>
					${nodewidget.display(node=node, header=None)}
				</tr>
			</tbody>
		</table>
		</td>
		</tr>
		</tbody>
	</table>
  </div>

</html>
